"""Allowlisted WAAS default origins; no DNS, header, rule or certificate storage."""
import ipaddress
import hashlib
import re
from urllib.parse import urlsplit


def literal_ip(value):
    try:
        if not isinstance(value,str) or '%' in value:return None
        return str(ipaddress.ip_address(value))
    except ValueError:return None


def origin_host(value):
    """Keep only a validated IP/hostname; discard credentials, paths and queries."""
    if not isinstance(value,str) or any(ord(c)<32 for c in value):return None
    value=value.strip()
    direct=literal_ip(value)
    if direct:return direct
    try:
        host=urlsplit(value if '://' in value else '//'+value).hostname
        if not host:return None
        direct=literal_ip(host)
        if direct:return direct
        host=host.rstrip('.').encode('idna').decode('ascii').lower()
        labels=host.split('.')
        if len(host)>253 or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',p) for p in labels):return None
        return host
    except (ValueError,UnicodeError):return None


def collect_edge_waf(call,add,snapshot,compartment):
    for summary in sorted(call('waas','list_waas_policies',compartment_id=compartment) or [],key=lambda p:p.id):
        detail=call('waas','get_waas_policy',waas_policy_id=summary.id)
        selected={};origins=[]
        config=getattr(detail,'waf_config',None)
        primary=getattr(config,'origin',None)
        if primary:selected.setdefault(primary,set()).add('WaasPolicy.waf_config.origin')
        groups=getattr(detail,'origin_groups',None) or {}
        source=getattr(detail,'origins',None) or {}
        for key in getattr(config,'origin_groups',None) or []:
            group=groups.get(key)
            members=getattr(group,'origins',None) or []
            if not members:selected.setdefault('missing-group:'+key,set()).add('WaasPolicy.waf_config.origin_groups[]')
            for member in members:
                if member.origin:selected.setdefault(member.origin,set()).add('WaasPolicy.waf_config.origin_groups[] → WaasPolicy.origin_groups[].origins[].origin')
        for key,evidence in sorted(selected.items()):
            obj=source.get(key)
            def port(field):
                value=getattr(obj,field,None)
                return value if isinstance(value,int) and not isinstance(value,bool) and 0<=value<=65535 else None
            origins.append({'key':key,'host':origin_host(getattr(obj,'uri',None)),
                'http_port':port('http_port'),'https_port':port('https_port'),
                'selected_by':sorted(evidence)})
        add(summary,'edge_waf',origins=origins,
            origin_status='unavailable' if detail is None else ('ok' if selected else 'not_configured'),
            lifecycle_state=getattr(detail or summary,'lifecycle_state',None))


def origin_targets(resource,resources,redacted=False):
    """Return exact-configured relations and logical unresolved origin nodes."""
    by_id={r['id']:r for r in resources};public={}
    for r in resources:
        addresses=[];target=r['id']
        if r['kind'] in ('lb','nlb'):
            addresses=[a.get('ip_address') for a in r.get('ip_addresses',[]) if isinstance(a,dict) and a.get('is_public') is True]
        elif r['kind']=='vnic' and by_id.get(r.get('instance_id'),{}).get('kind')=='compute':
            addresses=[r.get('public_ip')];target=r['instance_id']
        for address in addresses:
            ip=literal_ip(address)
            if ip:public.setdefault(ip,set()).add(target)
    items=resource.get('origins',[])
    if resource.get('origin_status')=='unavailable':items=[{'key':'unavailable','host':None,'selected_by':['GetWaasPolicy unavailable']}]
    extra={};relations={}
    for item in items:
        host=item.get('host');matches=public.get(literal_ip(host),set())
        if len(matches)==1:target=next(iter(matches))
        else:
            target=resource['id']+'/origin/'+hashlib.sha256(item['key'].encode('utf-8')).hexdigest()
            extra[target]={'id':target,'kind':'edge_origin','name':'대상 미확인',
                'display_details':[] if redacted or not host else ['Origin: '+host]}
        evidence=set(item.get('selected_by',[]))|{'WaasPolicy.origins[].uri → unique observed public LB/Compute IP' if len(matches)==1 else 'WaasPolicy.origins[].uri → unresolved configured origin'}
        relations.setdefault(target,set()).update(evidence)
    return extra,[(target,'; '.join(sorted(evidence))) for target,evidence in sorted(relations.items())]

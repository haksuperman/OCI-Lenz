"""Local operational labels; optional redaction is for sharing only."""
import copy
import textwrap
from .model import graph


def scope_title(snapshot):
    scope=snapshot['scope'];redacted=snapshot.get('presentation',{}).get('redacted')
    tenancy='Hidden' if redacted else scope.get('tenancy_name') or '이름 미확인'
    names=scope.get('compartment_names',{})
    compartments=[('Compartment '+str(i+1)) if redacted else names.get(key) or ('이름 미확인 ('+str(i+1)+')')
                  for i,key in enumerate(scope.get('compartments',[]))]
    return 'Tenancy: '+tenancy+'\nCompartment: '+(', '.join(compartments) or '이름 미확인')+' | Region: '+scope['region']


def resource_label(resource,width=22):
    lines=[resource['name'],*resource.get('display_details',[])]
    return '\n'.join(part for line in lines for part in (textwrap.wrap(line,width=width,break_long_words=True,break_on_hyphens=False) or ['']))


def network_label(resource,prefix):
    lines=[prefix+resource['name']]
    lines.extend(resource.get('display_details',[]))
    return '\n'.join(part for line in lines for part in (textwrap.wrap(line,width=44,break_on_hyphens=False) or ['']))


def prepare_display(snapshot,redact=False):
    result=copy.deepcopy(snapshot)
    result.setdefault('presentation',{})['redacted']=redact
    nodes,_=graph(result)
    aliases={'compute':'VM','lb':'LB','backend_set':'Backend set','vnic':'VNIC','vcn':'VCN','subnet':'Subnet','route':'RT','nsg':'NSG','nat':'NAT','internet':'IGW','service':'SGW','unknown':'대상 미확인'}
    alias={k:aliases.get(r['kind'],r['kind'])+' '+str(i+1) for i,(k,r) in enumerate(sorted(nodes.items()))}
    for r in result['resources']:
        r.pop('display_details',None)
        r.pop('summary_details',None)
        if redact:
            r['name']=alias[r['id']]
            for rule in r.get('rules',[]):
                if rule.get('destination')!='0.0.0.0/0':rule['destination']='Route destination hidden'
            continue
        details=[]
        sources=[r]
        if r['kind']=='compute':
            sources=[v for v in result['resources'] if v.get('instance_id')==r['id'] and v['kind']=='vnic']
        sources=sorted(sources,key=lambda v:(v.get('is_primary') is not True,v['id']))
        private=sorted({ip for src in sources for ip in src.get('private_ips',[]) if ip})
        public=sorted({src['public_ip'] for src in sources if src.get('public_ip')})
        details.extend('Private: '+ip for ip in private)
        details.extend('Public: '+ip for ip in public)
        preferred_private=next((src['primary_private_ip'] for src in sources if src.get('primary_private_ip')),next(iter(private),None))
        preferred_public=next((src['public_ip'] for src in sources if src.get('public_ip')),None)
        summary=[]
        if preferred_private:summary.append('Private: '+preferred_private)
        if preferred_public:summary.append('Public: '+preferred_public)
        for address in r.get('ip_addresses',[]):
            ip=address.get('ip_address') if isinstance(address,dict) else address
            if ip:
                prefix=('Public: ' if address.get('is_public') else 'Private: ') if isinstance(address,dict) else 'IP: '
                details.append(prefix+ip)
                if not any(d.startswith(prefix) for d in summary):summary.append(prefix+ip)
        cidrs=sorted(set(r.get('cidr_blocks',[]) or ([r['cidr_block']] if r.get('cidr_block') else [])))
        details.extend(cidrs)
        summary.extend(cidrs)
        listeners={}
        for listener in r.get('listeners',[]):
            protocol=listener.get('protocol') or 'UNKNOWN'
            if listener.get('port') is None:continue
            listeners.setdefault(protocol,set()).add(listener['port'])
            label='Listener '+listener.get('name','')+' '+protocol+':'+str(listener['port'])
            if listener.get('default_backend_set_name'):label+=' → '+listener['default_backend_set_name']+' (default)'
            details.append(label)
        for protocol,ports in sorted(listeners.items()):summary.append('Listen '+protocol+': '+','.join(str(p) for p in sorted(ports)))
        if r['kind']=='backend_set':
            details.extend(sorted({str(b['ip_address'])+':'+str(b['port']) for b in r.get('backends',[])}))
            ports=sorted({b['port'] for b in r.get('backends',[])})
            if ports:summary.insert(0,'Backend ports: '+','.join(str(p) for p in ports))
        r['display_details']=details
        r['summary_details']=summary
    if redact:
        for i,g in enumerate(result.get('presentation',{}).get('groups',[])):
            g['label']='Shared services' if g.get('role')=='shared' else 'Service '+str(i+1)
    return result

"""Read-only File Storage, API Gateway and Functions metadata and evidence."""
from types import SimpleNamespace as N
from urllib.parse import urlsplit
from .managed_data import address
from .edge_waf import origin_host

KINDS=frozenset(('file_system','mount_target','file_export','functions_application','function','api_gateway','api_deployment'))
NETWORK_EVIDENCE={
 'mount_target':{'subnet_id':'MountTargetSummary.subnet_id','nsg_ids':'MountTargetSummary.nsg_ids[]'},
 'functions_application':{'subnet_ids':'ApplicationSummary.subnet_ids[]','nsg_ids':'ApplicationSummary.network_security_group_ids[]'},
 'api_gateway':{'subnet_id':'Gateway.subnet_id','nsg_ids':'Gateway.network_security_group_ids[]'},
}


def primary_subnet(resource,nodes):
    kind=resource['kind']
    if kind=='function':
        owner=nodes.get(resource.get('application_id'),{})
        return sorted(owner.get('subnet_ids') or [])[0] if owner.get('kind')=='functions_application' and owner.get('subnet_ids') else None
    if kind=='api_deployment':
        owner=nodes.get(resource.get('api_gateway_id'),{})
        return owner.get('subnet_id') if owner.get('kind')=='api_gateway' else None
    if kind=='file_export':
        owners=[r for r in nodes.values() if r['kind']=='mount_target' and r.get('export_set_id') and r['export_set_id']==resource.get('export_set_id')]
        return owners[0].get('subnet_id') if len(owners)==1 else None
    return resource.get('subnet_id') or next(iter(sorted(resource.get('subnet_ids') or [])),None)


def compartment_resource(resource,nodes):
    from .regional_services import REGIONAL_KINDS
    if resource['kind']=='oke_cluster':
        from .oke import network_parent
        return network_parent(resource,nodes) is None
    return resource['kind'] in REGIONAL_KINDS or (resource['kind'] in KINDS and nodes.get(primary_subnet(resource,nodes),{}).get('kind')!='subnet')


def collect_file_storage(call,add,snapshot,compartment):
    ads=call('identity','list_availability_domains',compartment_id=compartment)
    if not ads:
        for api in ('list_file_systems','list_mount_targets'):
            snapshot['coverage'].append({'region':snapshot['scope']['region'],'compartment':compartment,'service':'fss','api':api,'status':'skipped','reason':'availability_domains_unavailable' if ads is None else 'no_availability_domains_returned'})
    for ad in sorted(ads or [],key=lambda a:a.name):
        for obj in call('fss','list_file_systems',compartment_id=compartment,availability_domain=ad.name) or []:
            add(obj,'file_system',compartment_id=getattr(obj,'compartment_id',None) or compartment,availability_domain=ad.name,lifecycle_state=getattr(obj,'lifecycle_state',None))
        for obj in call('fss','list_mount_targets',compartment_id=compartment,availability_domain=ad.name) or []:
            ips=[];failed=False
            for api,field,arg in [('get_private_ip','private_ip_ids','private_ip_id'),('get_ipv6','mount_target_ipv6_ids','ipv6_id')]:
                for key in sorted(set(getattr(obj,field,None) or [])):
                    detail=call('network',api,**{arg:key});ip=address(getattr(detail,'ip_address',None))
                    failed|=detail is None
                    if ip:ips.append(ip)
            ips=sorted(set(ips))
            add(obj,'mount_target',compartment_id=getattr(obj,'compartment_id',None) or compartment,
                subnet_id=getattr(obj,'subnet_id',None),nsg_ids=getattr(obj,'nsg_ids',None) or [],
                export_set_id=getattr(obj,'export_set_id',None),private_ips=ips,primary_private_ip=next(iter(ips),None),
                address_status='unavailable' if failed else ('ok' if ips else 'not_reported'),lifecycle_state=getattr(obj,'lifecycle_state',None))
    for obj in call('fss','list_exports',compartment_id=compartment) or []:
        add(N(id=obj.id,display_name='Export'),'file_export',compartment_id=compartment,
            file_system_id=getattr(obj,'file_system_id',None),export_set_id=getattr(obj,'export_set_id',None),lifecycle_state=getattr(obj,'lifecycle_state',None))


def collect_functions(call,add,compartment):
    for app in call('functions','list_applications',compartment_id=compartment) or []:
        owner=getattr(app,'compartment_id',None) or compartment
        add(app,'functions_application',compartment_id=owner,subnet_ids=sorted(set(getattr(app,'subnet_ids',None) or [])),
            nsg_ids=getattr(app,'network_security_group_ids',None) or [],lifecycle_state=getattr(app,'lifecycle_state',None))
        for fn in call('functions','list_functions',application_id=app.id) or []:
            actual=getattr(fn,'application_id',None)
            add(fn,'function',compartment_id=getattr(fn,'compartment_id',None) or owner,application_id=actual or app.id,
                application_evidence='FunctionSummary.application_id' if actual else 'ListFunctions.application_id request filter',lifecycle_state=getattr(fn,'lifecycle_state',None))


def backend_references(backend,unsupported,depth=0):
    if backend is None:return []
    kind=getattr(backend,'type',None)
    if kind=='ORACLE_FUNCTIONS_BACKEND':return [{'type':kind,'function_id':getattr(backend,'function_id',None),'evidence':'Deployment.specification.routes[].backend.function_id'}]
    if kind=='HTTP_BACKEND':
        url=getattr(backend,'url',None);host=origin_host(url)
        try:port=urlsplit(url).port if isinstance(url,str) else None
        except ValueError:port=None
        return [{'type':kind,'host':host,'port':port,'evidence':'Deployment.specification.routes[].backend.url (sanitized host only)'}]
    if kind=='DYNAMIC_ROUTING_BACKEND' and depth<16:
        refs=[]
        for entry in getattr(backend,'routing_backends',None) or []:
            for item in backend_references(getattr(entry,'backend',None),unsupported,depth+1):
                item['evidence']='Deployment.specification.routes[].backend.routing_backends[].backend → '+item['evidence']
                if item not in refs:refs.append(item)
        return refs
    if kind not in ('STOCK_RESPONSE_BACKEND','OAUTH2_LOGIN_BACKEND','OAUTH2_LOGOUT_BACKEND'):
        unsupported.add('DYNAMIC_ROUTING_BACKEND_DEPTH_LIMIT' if depth>=16 else 'UNKNOWN_BACKEND_TYPE')
    return []


def collect_api_gateway(call,add,snapshot,compartment):
    for summary in call('apigw','list_gateways',compartment_id=compartment) or []:
        detail=call('apigw','get_gateway',gateway_id=summary.id)
        def observed(field):
            value=getattr(detail,field,None)
            return value if value is not None else getattr(summary,field,None)
        kind=observed('endpoint_type');ips=sorted({address(a.ip_address) for a in observed('ip_addresses') or [] if address(a.ip_address)})
        data={'compartment_id':getattr(summary,'compartment_id',None) or compartment,'subnet_id':observed('subnet_id'),
              'nsg_ids':observed('network_security_group_ids') or [],'endpoint_type':kind,'detail_status':'ok' if detail is not None else 'unavailable',
              'lifecycle_state':observed('lifecycle_state'),'private_ips':ips if kind=='PRIVATE' else [],
              'primary_private_ip':next(iter(ips),None) if kind=='PRIVATE' else None,
              'public_ip':next(iter(ips),None) if kind=='PUBLIC' else None,
              'ip_addresses':[{'ip_address':ip,'is_public':kind=='PUBLIC'} for ip in ips] if kind in ('PUBLIC','PRIVATE') else ips,
              'network_evidence':{field:('Gateway' if getattr(detail,api,None) is not None else 'GatewaySummary')+'.'+api+('[]' if field=='nsg_ids' else '') for field,api in [('subnet_id','subnet_id'),('nsg_ids','network_security_group_ids')]}}
        add(summary,'api_gateway',**data)
    for summary in call('apideploy','list_deployments',compartment_id=compartment) or []:
        detail=call('apideploy','get_deployment',deployment_id=summary.id);refs=[];unsupported=set()
        spec=getattr(detail,'specification',None)
        for route in getattr(spec,'routes',None) or []:
            for item in backend_references(getattr(route,'backend',None),unsupported):
                if item not in refs:refs.append(item)
        add(summary,'api_deployment',compartment_id=getattr(summary,'compartment_id',None) or compartment,
            api_gateway_id=getattr(detail,'gateway_id',None) or getattr(summary,'gateway_id',None),
            gateway_evidence='Deployment.gateway_id' if getattr(detail,'gateway_id',None) else 'DeploymentSummary.gateway_id',backends=refs,
            backends_status='unavailable' if detail is None or spec is None else 'ok',lifecycle_state=getattr(summary,'lifecycle_state',None))
        if unsupported:snapshot['coverage'].append({'region':snapshot['scope']['region'],'compartment':compartment,'service':'apideploy','status':'unsupported','feature':'backend_type','resource_id':summary.id,'types':sorted(unsupported)})


def api_backend_targets(resource,resources):
    nodes={r['id']:r for r in resources};gateway=nodes.get(resource.get('api_gateway_id'),{})
    vcn=nodes.get(gateway.get('subnet_id'),{}).get('vcn_id');results={}
    for i,ref in enumerate(resource.get('backends') or []):
        target=None;evidence=ref.get('evidence','')
        if ref.get('type')=='ORACLE_FUNCTIONS_BACKEND':
            key=ref.get('function_id')
            if key and (key not in nodes or nodes[key]['kind']=='function'):target=key
        elif ref.get('type')=='HTTP_BACKEND':
            ip=address(ref.get('host'));matches=set()
            if ip:
                for r in resources:
                    scope=r.get('vcn_id') or nodes.get(r.get('subnet_id'),{}).get('vcn_id')
                    if r['kind']=='vnic' and nodes.get(r.get('instance_id'),{}).get('kind')=='compute':
                        if ip==address(r.get('public_ip')) or (vcn is not None and scope==vcn and ip in r.get('private_ips',[])):matches.add(r['instance_id'])
                    if r['kind'] in ('lb','nlb'):
                        subnets=r.get('subnet_ids') or [r.get('subnet_id')]
                        vcns={nodes.get(s,{}).get('vcn_id') for s in subnets}
                        if any(address(a.get('ip_address'))==ip and (a.get('is_public') is True or (vcn is not None and vcn in vcns)) for a in r.get('ip_addresses',[]) if isinstance(a,dict)):matches.add(r['id'])
                if len(matches)==1:target=next(iter(matches))
            evidence+=' → unique observed public endpoint or same-VCN VNIC/LB IP' if target else ' → unresolved configured backend'
        target=target or ('api-backend:'+resource['id']+':'+str(i))
        results.setdefault(target,set()).add(evidence)
    return [(target,'; '.join(sorted(evidence))) for target,evidence in sorted(results.items())]

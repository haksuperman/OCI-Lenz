"""Shared LB presentation roles and scoped read-only Network Load Balancer data."""
LOAD_BALANCER_KINDS=('lb','nlb')


def subnet_ids(resource):
    return resource.get('subnet_ids',[]) or ([resource['subnet_id']] if resource.get('subnet_id') else [])


def match_backend_ip(backend,resources,nodes,vcns):
    """Shared LB/NLB configured-address relation, independent of OCID lookups."""
    from .managed_data import address,KINDS,ENDPOINT_FIELDS
    ip=address(backend.get('ip_address'))
    matches=[r for r in resources if r['kind']=='vnic' and ip and
             (r.get('vcn_id') or nodes.get(r.get('subnet_id'),{}).get('vcn_id')) in vcns and
             ip in {address(value) for value in r.get('private_ips',[])}]
    endpoints=[r for r in resources if r['kind'] in ('mysql_db_system','autonomous_database','cloud_vm_cluster','exadb_vm_cluster',*KINDS) and ip and
               nodes.get(r.get('subnet_id'),{}).get('vcn_id') in vcns and ip in {address(value) for value in r.get('private_ips',[])}]
    candidates=matches+endpoints
    evidence='BackendSet.backends[].ip_address → unique VNIC/PrivateIp in LB VCN'
    if endpoints:evidence='BackendSet.backends[].ip_address → unique observed VNIC or database endpoint / managed-service endpoint in LB VCN'
    if len(candidates)!=1:return None,evidence
    chosen=candidates[0]
    if chosen['kind'] in ENDPOINT_FIELDS:evidence='BackendSet.backends[].ip_address → unique same-VCN '+ENDPOINT_FIELDS[chosen['kind']]
    return chosen.get('instance_id') or chosen.get('db_node_id') or chosen['id'],evidence


def collect_nlb(call,add,snapshot,compartment):
    for nlb in call('nlb','list_network_load_balancers',compartment_id=compartment) or []:
        listeners=call('nlb','list_listeners',nlb.id)
        # Lists contain this configuration too; retain it if child reads fail.
        if listeners is None:listeners=list((getattr(nlb,'listeners',None) or {}).values())
        add(nlb,'nlb',subnet_id=nlb.subnet_id,nsg_ids=nlb.network_security_group_ids or [],
            ip_addresses=[{'ip_address':ip.ip_address,'is_public':ip.is_public} for ip in nlb.ip_addresses or []],
            listeners=[{'name':l.name,'protocol':l.protocol,'port':l.port,
                'default_backend_set_name':l.default_backend_set_name} for l in listeners],
            lifecycle_state=nlb.lifecycle_state)
        for bs in call('nlb','list_backend_sets',nlb.id) or []:
            backends=call('nlb','list_backends',nlb.id,bs.name)
            snapshot['resources'].append({'id':nlb.id+'/backend-set/'+bs.name,
                'kind':'backend_set','name':bs.name,'lb_id':nlb.id,
                'lb_id_evidence':'NetworkLoadBalancer BackendSet owner request network_load_balancer_id',
                'backends_status':'ok' if backends is not None else 'unavailable',
                'backends':[{'ip_address':b.ip_address,'target_id':b.target_id,'port':b.port} for b in backends or []]})

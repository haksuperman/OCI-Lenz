"""Shared LB presentation roles and scoped read-only Network Load Balancer data."""
LOAD_BALANCER_KINDS=('lb','nlb')


def subnet_ids(resource):
    return resource.get('subnet_ids',[]) or ([resource['subnet_id']] if resource.get('subnet_id') else [])


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
                'backends':[{'ip_address':b.ip_address,'target_id':b.target_id,'port':b.port} for b in backends or []]})

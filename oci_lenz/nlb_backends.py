"""Scoped NLB reference enrichment. No data-plane or out-of-scope enumeration."""
from .managed_data import address


def resolved_owner(vnic,nodes):
    owner=vnic.get('instance_id') or vnic.get('db_node_id')
    return owner if nodes.get(owner,{}).get('kind') in ('compute','db_node') else None


def explicit_target(backend,resources):
    """Use an already observed exact identity; IP matching is shared with LB."""
    nodes={r['id']:r for r in resources};target=backend.get('target_id')
    if nodes.get(target,{}).get('kind')=='compute':return target,'NetworkLoadBalancer Backend.target_id → Instance.id'
    nics=[r for r in resources if r['kind']=='vnic' and target in r.get('private_ip_ids',[])]
    if len(nics)==1:
        return resolved_owner(nics[0],nodes),'NetworkLoadBalancer Backend.target_id → PrivateIp.id → PrivateIp.vnic_id → ListVnicAttachments / VnicAttachment.instance_id'
    return None,None


def resolve_nlb_backends(call,add,snapshot,compartment):
    """Fill absent target metadata only inside the requested compartment."""
    cache={}
    def read(service,api,*args,**kwargs):
        key=(service,api,args,tuple(sorted(kwargs.items())))
        if key not in cache:
            before=len(snapshot['coverage']);obj=call(service,api,*args,**kwargs)
            status=snapshot['coverage'][-1]['status'] if len(snapshot['coverage'])>before else ('ok' if obj is not None else 'failed')
            cache[key]=(obj,status)
        return cache[key]
    for bs in list(snapshot['resources']):
        nodes={r['id']:r for r in snapshot['resources']}
        if bs['kind']!='backend_set' or nodes.get(bs.get('lb_id'),{}).get('kind')!='nlb':continue
        for backend in bs.get('backends',[]):
            def lookup(service,api,*args,**kwargs):
                backend['target_resolution_stage']=api
                return read(service,api,*args,**kwargs)
            nodes={r['id']:r for r in snapshot['resources']};target=backend.get('target_id')
            if not target:continue
            known_nics=[r for r in snapshot['resources'] if r['kind']=='vnic' and target in r.get('private_ip_ids',[])]
            if len(known_nics)>1:backend['target_resolution_status']='ambiguous_private_ip';continue
            found=nodes.get(target,{}).get('kind')=='compute' or (len(known_nics)==1 and resolved_owner(known_nics[0],nodes))
            if found:backend.update(target_resolution_status='resolved',target_resolution_stage='inventory');continue
            from .load_balancers import match_backend_ip,subnet_ids
            lb=nodes[bs['lb_id']];vcns={nodes.get(key,{}).get('vcn_id') for key in subnet_ids(lb)}-{None}
            ip_match,_=match_backend_ip(backend,snapshot['resources'],nodes,vcns)
            if ip_match in nodes:
                backend.update(target_resolution_status='ip_match',target_resolution_stage='inventory');continue
            if address(backend.get('ip_address')):
                backend.update(target_resolution_status='ip_registration',target_resolution_stage='inventory');continue
            if target.startswith('ocid1.instance.'):
                obj,status=lookup('compute','get_instance',instance_id=target)
                if obj is None:backend['target_resolution_status']=status;continue
                if getattr(obj,'compartment_id',None)!=compartment:backend['target_resolution_status']='outside_scope';continue
                if getattr(obj,'id',None)!=target:backend['target_resolution_status']='incomplete';continue
                add(obj,'compute',compartment_id=compartment);backend['target_resolution_status']='resolved';continue
            if not target.startswith('ocid1.privateip.'):
                backend['target_resolution_status']='unsupported_target_type';continue
            obj,status=lookup('network','get_private_ip',private_ip_id=target)
            if obj is None:backend['target_resolution_status']=status;continue
            if getattr(obj,'compartment_id',None)!=compartment:backend['target_resolution_status']='outside_scope';continue
            vid=getattr(obj,'vnic_id',None);subnet=getattr(obj,'subnet_id',None);ip=address(getattr(obj,'ip_address',None))
            if getattr(obj,'id',None)!=target or not vid or not subnet or not ip:
                backend['target_resolution_status']='incomplete';continue
            if address(backend.get('ip_address')) and address(backend['ip_address'])!=ip:
                backend['target_resolution_status']='conflicting_identity';continue
            backend['target_ip_address']=ip  # Observed PrivateIp.ip_address; preserve the raw registration field.
            existing=nodes.get(vid)
            if existing and (existing['kind']!='vnic' or existing.get('subnet_id')!=subnet):
                backend['target_resolution_status']='conflicting_identity';continue
            vnic=None
            if existing is None:
                vnic,status=lookup('network','get_vnic',vid)
                if vnic is None:backend['target_resolution_status']=status;continue
                if getattr(vnic,'id',None)!=vid or getattr(vnic,'subnet_id',None)!=subnet:
                    backend['target_resolution_status']='conflicting_identity';continue
            owner=resolved_owner(existing or {},nodes)
            if owner is None:
                attachments,status=lookup('compute','list_vnic_attachments',compartment_id=compartment,vnic_id=vid)
                if attachments is None:backend['target_resolution_status']=status;continue
                owners={a.instance_id for a in attachments if a.vnic_id==vid and a.instance_id}
                if len(owners)!=1:backend['target_resolution_status']='ambiguous_attachment' if owners else 'attachment_not_found';continue
                owner=next(iter(owners))
                if nodes.get(owner,{}).get('kind')!='compute':
                    instance,status=lookup('compute','get_instance',instance_id=owner)
                    if instance is None:backend['target_resolution_status']=status;continue
                    if getattr(instance,'compartment_id',None)!=compartment:backend['target_resolution_status']='outside_scope';continue
                    if getattr(instance,'id',None)!=owner:backend['target_resolution_status']='incomplete';continue
                    add(instance,'compute',compartment_id=compartment)
            if existing:
                existing['private_ip_ids']=sorted(set(existing.get('private_ip_ids',[]))|{target})
                existing['private_ips']=sorted(set(existing.get('private_ips',[]))|{ip})
                if not resolved_owner(existing,nodes):existing['instance_id']=owner
            else:
                primary=address(getattr(vnic,'private_ip',None))
                add(vnic,'vnic',compartment_id=compartment,instance_id=owner,subnet_id=subnet,
                    vcn_id=nodes.get(subnet,{}).get('vcn_id'),private_ip_ids=[target],private_ips=sorted({ip}|({primary} if primary else set())),
                    primary_private_ip=primary,public_ip=address(getattr(vnic,'public_ip',None)),nsg_ids=getattr(vnic,'nsg_ids',None) or [],is_primary=getattr(vnic,'is_primary',None))
            backend['target_resolution_status']='resolved'

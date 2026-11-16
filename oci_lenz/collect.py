"""Read-only OCI SDK collector. Only allowlisted response fields leave this module."""

def collect(profile,region,compartment,config_file=None,vcn_id=None):
    import oci
    if any(c in compartment for c in ("'", '\n', '\r')): raise ValueError('invalid compartment')
    cfg=oci.config.from_file(config_file or oci.config.DEFAULT_LOCATION,profile);cfg['region']=region
    retry=oci.retry.RetryStrategyBuilder(max_attempts_check=True,max_attempts=3,total_elapsed_time_check=True,total_elapsed_time_seconds=30).get_retry_strategy()
    clients={k:c(cfg,retry_strategy=retry) for k,c in {'identity':oci.identity.IdentityClient,'network':oci.core.VirtualNetworkClient,'compute':oci.core.ComputeClient,'lb':oci.load_balancer.LoadBalancerClient,'search':oci.resource_search.ResourceSearchClient}.items()}
    s={'version':1,'scope':{'region':region,'compartments':[compartment]},'resources':[],'coverage':[]}
    def call(service,method,*args,**kwargs):
        entry={'region':region,'compartment':compartment,'service':service,'api':method}
        try:
            fn=getattr(clients[service],method)
            if method.startswith(('list_','search_')): data=oci.pagination.list_call_get_all_results(fn,*args,**kwargs).data
            else:data=fn(*args,**kwargs).data
            count=len(data) if isinstance(data,list) else 1
            entry.update(status='ok',count=count)
            return data
        except oci.exceptions.ServiceError as exc:entry.update(status='permission_denied' if exc.status in (401,403) else ('not_found_or_not_authorized' if exc.status==404 else 'failed'),http_status=exc.status)
        except Exception:entry.update(status='failed')
        finally:s['coverage'].append(entry)
        return None
    def add(obj,kind,**fields):
        if obj is not None:
            if getattr(obj,'compartment_id',None):fields.setdefault('compartment_id',obj.compartment_id)
            s['resources'].append(dict(id=obj.id,kind=kind,name=getattr(obj,'display_name',None) or kind,**fields))
    call('identity','list_region_subscriptions',cfg['tenancy'])
    call('identity','list_compartments',cfg['tenancy'],compartment_id_in_subtree=True,access_level='ACCESSIBLE')
    vcns=call('network','list_vcns',compartment) or []
    for v in vcns:
        if not vcn_id or v.id==vcn_id:add(v,'vcn',cidr_blocks=getattr(v,'cidr_blocks',None) or ([v.cidr_block] if getattr(v,'cidr_block',None) else []))
    for api,kind in [('list_subnets','subnet'),('list_route_tables','route'),('list_network_security_groups','nsg'),('list_nat_gateways','nat'),('list_internet_gateways','internet'),('list_service_gateways','service')]:
        for r in call('network',api,compartment_id=compartment) or []:
            if vcn_id and r.vcn_id!=vcn_id:continue
            fields={'vcn_id':r.vcn_id}
            if kind=='subnet':fields.update(public=not r.prohibit_public_ip_on_vnic,route_table_id=r.route_table_id,cidr_block=getattr(r,'cidr_block',None))
            if kind=='route':fields['rules']=[{'destination':rr.destination,'network_entity_id':rr.network_entity_id} for rr in r.route_rules]
            add(r,kind,**fields)
    instances=call('compute','list_instances',compartment) or []
    attachments=call('compute','list_vnic_attachments',compartment) or []
    selected=set()
    subnets={r['id']:r for r in s['resources'] if r['kind']=='subnet'}
    for a in attachments:
        if not a.vnic_id:continue
        v=call('network','get_vnic',a.vnic_id)
        if v is None:continue
        subnet=subnets.get(v.subnet_id)
        if vcn_id and (not subnet or subnet['vcn_id']!=vcn_id):continue
        ips=call('network','list_private_ips',vnic_id=v.id)
        private_ips={p.ip_address for p in ips or [] if p.ip_address}
        if v.private_ip:private_ips.add(v.private_ip)
        add(v,'vnic',instance_id=a.instance_id,subnet_id=v.subnet_id,vcn_id=subnet['vcn_id'] if subnet else None,nsg_ids=v.nsg_ids or [],private_ips=sorted(private_ips),public_ip=getattr(v,'public_ip',None),primary_private_ip=v.private_ip,is_primary=getattr(v,'is_primary',None))
        selected.add(a.instance_id)
    for r in instances:
        if not vcn_id or r.id in selected:add(r,'compute')
    for lb in call('lb','list_load_balancers',compartment) or []:
        if vcn_id and not any(subnets.get(i,{}).get('vcn_id')==vcn_id for i in lb.subnet_ids):continue
        detail=call('lb','get_load_balancer',lb.id)
        listeners=getattr(detail,'listeners',None) if detail is not None else None
        if listeners is None:listeners=getattr(lb,'listeners',None) or {}
        listener_fields=[{'name':name,'protocol':listener.protocol,'port':listener.port,'default_backend_set_name':listener.default_backend_set_name} for name,listener in sorted(listeners.items())]
        add(lb,'lb',subnet_ids=lb.subnet_ids,nsg_ids=lb.network_security_group_ids or [],ip_addresses=[{'ip_address':ip.ip_address,'is_public':ip.is_public} for ip in getattr(lb,'ip_addresses',None) or []],listeners=listener_fields)
        sets=call('lb','list_backend_sets',lb.id)
        for bs in sets or []:
            backends=call('lb','list_backends',lb.id,bs.name)
            s['resources'].append({'id':lb.id+'/backend-set/'+bs.name,'kind':'backend_set','name':bs.name,'lb_id':lb.id,'backends':[{'ip_address':b.ip_address,'port':b.port} for b in backends or []]})
    # Search counts are inventory evidence only, never inferred graph relationships.
    query=oci.resource_search.models.StructuredSearchDetails(query=f"query all resources where compartmentId = '{compartment}'")
    inventory=call('search','search_resources',query)
    if inventory is not None:
        mapping={'Vcn':'vcn','Subnet':'subnet','Instance':'compute','LoadBalancer':'lb','NatGateway':'nat','InternetGateway':'internet','ServiceGateway':'service','NetworkSecurityGroup':'nsg','RouteTable':'route'}
        s['coverage'][-1]['inventory_comparison']={kind:{'search':sum(getattr(r,'resource_type',None)==api_type for r in inventory),'collected':sum(r['kind']==kind for r in s['resources'])} for api_type,kind in mapping.items()}
        s['coverage'][-1]['comparison_note']='Search visibility/indexing may differ; differences do not establish missing resources.'
    for kind in ('database','oke','drg','peering'):
        s['coverage'].append({'region':region,'compartment':compartment,'service':kind,'status':'unsupported'})
    return s

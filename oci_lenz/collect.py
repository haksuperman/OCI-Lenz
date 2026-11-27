"""Read-only OCI SDK collector. Only allowlisted response fields leave this module."""

def collect(profile,region,compartment,config_file=None):
    import oci
    if any(c in compartment for c in ("'", '\n', '\r')): raise ValueError('invalid compartment')
    cfg=oci.config.from_file(config_file or oci.config.DEFAULT_LOCATION,profile);cfg['region']=region
    retry=oci.retry.RetryStrategyBuilder(max_attempts_check=True,max_attempts=3,total_elapsed_time_check=True,total_elapsed_time_seconds=30).get_retry_strategy()
    clients={k:c(cfg,retry_strategy=retry) for k,c in {'identity':oci.identity.IdentityClient,'network':oci.core.VirtualNetworkClient,'compute':oci.core.ComputeClient,'lb':oci.load_balancer.LoadBalancerClient,'nlb':oci.network_load_balancer.NetworkLoadBalancerClient,'waf':oci.waf.WafClient,'waas':oci.waas.WaasClient,'search':oci.resource_search.ResourceSearchClient,'database':oci.database.DatabaseClient,'mysql':oci.mysql.DbSystemClient,'redis':oci.redis.RedisClusterClient,'psql':oci.psql.PostgresqlClient,'opensearch':oci.opensearch.OpensearchClusterClient,'nosql':oci.nosql.NosqlClient,'object_storage':oci.object_storage.ObjectStorageClient,'artifacts':oci.artifacts.ArtifactsClient,'devops':oci.devops.DevopsClient,'goldengate':oci.golden_gate.GoldenGateClient,'oke':oci.container_engine.ContainerEngineClient,'fss':oci.file_storage.FileStorageClient,'functions':oci.functions.FunctionsManagementClient,'apigw':oci.apigateway.GatewayClient,'apideploy':oci.apigateway.DeploymentClient}.items()}
    s={'version':1,'scope':{'region':region,'compartments':[compartment]},'resources':[],'coverage':[]}
    def call(service,method,*args,**kwargs):
        entry={'region':region,'compartment':compartment,'service':service,'api':method}
        scoped={key:value for key,value in kwargs.items() if key in ('db_system_id','vm_cluster_id','exadata_infrastructure_id','waas_policy_id','redis_cluster_id','opensearch_cluster_id','deployment_id','cluster_id','node_pool_id','application_id','gateway_id','availability_domain','private_ip_id','ipv6_id','instance_id','vnic_id')}
        if scoped:entry['request_scope']=scoped
        try:
            fn=getattr(clients[service],method)
            if method.startswith(('list_','search_')): data=oci.pagination.list_call_get_all_results(fn,*args,**kwargs).data
            else:data=fn(*args,**kwargs).data
            # NLB/WAF APIs use Collection wrappers; support raw and flattened paginator results.
            if service in ('nlb','waf','redis','psql','opensearch','nosql','artifacts','devops','goldengate','fss','functions','apigw','apideploy') and method.startswith('list_') and not isinstance(data,list):data=data.items
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
            s['resources'].append(dict(id=obj.id,kind=kind,name=getattr(obj,'display_name',None) or getattr(obj,'name',None) or kind,**fields))
    call('identity','list_region_subscriptions',cfg['tenancy'])
    tenancy=call('identity','get_tenancy',cfg['tenancy'])
    if getattr(tenancy,'name',None):s['scope']['tenancy_name']=tenancy.name
    compartments=call('identity','list_compartments',cfg['tenancy'],compartment_id_in_subtree=True,access_level='ACCESSIBLE') or []
    # Persist only the selected scope's name, never all accessible identity data.
    selected=next((c for c in compartments if c.id==compartment),None)
    if compartment==cfg['tenancy'] and getattr(tenancy,'name',None):selected=tenancy
    if selected is None:selected=call('identity','get_compartment',compartment)
    if getattr(selected,'name',None):s['scope']['compartment_names']={compartment:selected.name}
    vcns=call('network','list_vcns',compartment) or []
    for v in vcns:
        add(v,'vcn',cidr_blocks=getattr(v,'cidr_blocks',None) or ([v.cidr_block] if getattr(v,'cidr_block',None) else []))
    for api,kind in [('list_subnets','subnet'),('list_route_tables','route'),('list_network_security_groups','nsg'),('list_nat_gateways','nat'),('list_internet_gateways','internet'),('list_service_gateways','service')]:
        for r in call('network',api,compartment_id=compartment) or []:
            fields={'vcn_id':r.vcn_id}
            if kind=='subnet':fields.update(public=not r.prohibit_public_ip_on_vnic,route_table_id=r.route_table_id,cidr_block=getattr(r,'cidr_block',None))
            if kind=='route':fields['rules']=[{'destination':rr.destination,'network_entity_id':rr.network_entity_id} for rr in r.route_rules]
            add(r,kind,**fields)
    instances=call('compute','list_instances',compartment) or []
    attachments=call('compute','list_vnic_attachments',compartment) or []
    subnets={r['id']:r for r in s['resources'] if r['kind']=='subnet'}
    for a in attachments:
        if not a.vnic_id:continue
        v=call('network','get_vnic',a.vnic_id)
        if v is None:continue
        subnet=subnets.get(v.subnet_id)
        ips=call('network','list_private_ips',vnic_id=v.id)
        private_ips={p.ip_address for p in ips or [] if p.ip_address}
        if v.private_ip:private_ips.add(v.private_ip)
        add(v,'vnic',instance_id=a.instance_id,subnet_id=v.subnet_id,vcn_id=subnet['vcn_id'] if subnet else None,nsg_ids=v.nsg_ids or [],private_ips=sorted(private_ips),private_ip_ids=sorted({p.id for p in ips or [] if getattr(p,'id',None)}),public_ip=getattr(v,'public_ip',None),primary_private_ip=v.private_ip,is_primary=getattr(v,'is_primary',None))
    for r in instances:
        add(r,'compute')
    for lb in call('lb','list_load_balancers',compartment) or []:
        detail=call('lb','get_load_balancer',lb.id)
        listeners=getattr(detail,'listeners',None) if detail is not None else None
        if listeners is None:listeners=getattr(lb,'listeners',None) or {}
        listener_fields=[{'name':name,'protocol':listener.protocol,'port':listener.port,'default_backend_set_name':listener.default_backend_set_name} for name,listener in sorted(listeners.items())]
        add(lb,'lb',subnet_ids=lb.subnet_ids,nsg_ids=lb.network_security_group_ids or [],ip_addresses=[{'ip_address':ip.ip_address,'is_public':ip.is_public} for ip in getattr(lb,'ip_addresses',None) or []],listeners=listener_fields)
        sets=call('lb','list_backend_sets',lb.id)
        for bs in sets or []:
            backends=call('lb','list_backends',lb.id,bs.name)
            s['resources'].append({'id':lb.id+'/backend-set/'+bs.name,'kind':'backend_set','name':bs.name,'lb_id':lb.id,'backends_status':'ok' if backends is not None else 'unavailable','backends':[{'ip_address':b.ip_address,'port':b.port} for b in backends or []]})
    from .load_balancers import collect_nlb
    collect_nlb(call,add,s,compartment)
    from .waf import collect_waf
    collect_waf(call,add,s,compartment)
    from .edge_waf import collect_edge_waf
    collect_edge_waf(call,add,s,compartment)
    from .network import collect_network
    collect_network(call,add,s,compartment)
    from .vpn import collect_vpn
    collect_vpn(call,add,compartment)
    from .fastconnect import collect_fastconnect
    collect_fastconnect(call,add,compartment)
    from .database import collect_base_database
    collect_base_database(call,add,s,compartment)
    from .database_services import collect_mysql,collect_autonomous,collect_exacc,collect_exaci,collect_exascale
    collect_mysql(call,add,compartment)
    collect_autonomous(call,add,compartment)
    collect_exacc(call,add,s,compartment)
    collect_exaci(call,add,s,compartment)
    collect_exascale(call,add,s,compartment)
    from .managed_data import collect_managed_data
    collect_managed_data(call,add,compartment)
    from .nosql import collect_nosql
    collect_nosql(call,add,compartment)
    from .regional_services import collect_regional_services
    collect_regional_services(call,add,s,compartment)
    from .application_services import collect_file_storage,collect_functions,collect_api_gateway
    collect_file_storage(call,add,s,compartment)
    collect_functions(call,add,compartment)
    collect_api_gateway(call,add,s,compartment)
    from .nlb_backends import resolve_nlb_backends
    resolve_nlb_backends(call,add,s,compartment)
    from .oke import collect_oke
    collect_oke(call,add,s,compartment)
    # Search counts are inventory evidence only, never inferred graph relationships.
    query=oci.resource_search.models.StructuredSearchDetails(query=f"query all resources where compartmentId = '{compartment}'")
    inventory=call('search','search_resources',query)
    if inventory is not None:
        mapping={'Vcn':'vcn','Subnet':'subnet','Instance':'compute','LoadBalancer':'lb','NetworkLoadBalancer':'nlb','NatGateway':'nat','InternetGateway':'internet','ServiceGateway':'service','NetworkSecurityGroup':'nsg','RouteTable':'route'}
        s['coverage'][-1]['inventory_comparison']={kind:{'search':sum(getattr(r,'resource_type',None)==api_type for r in inventory),'collected':sum(r['kind']==kind for r in s['resources'])} for api_type,kind in mapping.items()}
        s['coverage'][-1]['comparison_note']='Search visibility/indexing may differ; differences do not establish missing resources.'
    for kind in ('database_catalog','drg_routing'):
        s['coverage'].append({'region':region,'compartment':compartment,'service':kind,'status':'unsupported'})
    return s

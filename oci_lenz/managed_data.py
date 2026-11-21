"""Read-only infrastructure metadata, never SQL/cache/search data or credentials."""
from ipaddress import ip_address

KINDS=('oci_cache','postgresql_db_system','opensearch_cluster')
ENDPOINT_FIELDS={
    'oci_cache':'RedisCluster.primary_endpoint_ip_address / replicas_endpoint_ip_address / discovery_endpoint_ip_address',
    'postgresql_db_system':'DbSystem.network_details.primary_db_endpoint_private_ip / ConnectionDetails.primary_db_endpoint.ip_address / reader_endpoint.ip_address / instance_endpoints[].endpoint.ip_address',
    'opensearch_cluster':'OpensearchCluster.opensearch_private_ip / opendashboard_private_ip',
}
EVIDENCE={
    'oci_cache':{'subnet_id':'RedisCluster.subnet_id','nsg_ids':'RedisCluster.nsg_ids[]'},
    'postgresql_db_system':{'subnet_id':'DbSystem.network_details.subnet_id','nsg_ids':'DbSystem.network_details.nsg_ids[]'},
    'opensearch_cluster':{'subnet_id':'OpensearchCluster.subnet_id','vcn_id':'OpensearchCluster.vcn_id','nsg_ids':'OpensearchCluster.nsg_id'},
}


def address(value):
    if not isinstance(value,str):return None
    try:return str(ip_address(value))
    except ValueError:return None


def collect_managed_data(call,add,compartment):
    for service,list_api,get_api,kind in (
        ('redis','list_redis_clusters','get_redis_cluster','oci_cache'),
        ('psql','list_db_systems','get_db_system','postgresql_db_system'),
        ('opensearch','list_opensearch_clusters','get_opensearch_cluster','opensearch_cluster')):
        for summary in call(service,list_api,compartment_id=compartment) or []:
            key={'redis':'redis_cluster_id','psql':'db_system_id','opensearch':'opensearch_cluster_id'}[service]
            detail=call(service,get_api,**{key:summary.id});obj=detail or summary
            # Prefer observed detail fields, but preserve summary network data
            # when a denied/partial Get does not provide them.
            def observed(name):
                value=getattr(obj,name,None)
                return value if value is not None else getattr(summary,name,None)
            endpoints=[]
            def endpoint(role,ip,instance=None):
                ip=address(ip)
                if ip is None:return
                item={'role':role,'ip_address':ip}
                if instance:item['instance_id']=instance
                if item not in endpoints:endpoints.append(item)
            if service=='redis':
                subnet=observed('subnet_id');nsgs=observed('nsg_ids') or []
                for role,field in [('primary','primary_endpoint_ip_address'),('replica','replicas_endpoint_ip_address'),('discovery','discovery_endpoint_ip_address')]:
                    endpoint(role,observed(field))
            elif service=='psql':
                network=observed('network_details')
                subnet=getattr(network,'subnet_id',None);nsgs=getattr(network,'nsg_ids',None) or []
                fallback_primary=getattr(network,'primary_db_endpoint_private_ip',None)
                connection=call('psql','get_connection_details',db_system_id=summary.id)
                if connection is not None:
                    for role,field in [('primary','primary_db_endpoint'),('reader','reader_endpoint')]:
                        endpoint(role,getattr(getattr(connection,field,None),'ip_address',None))
                    if not any(e['role']=='primary' for e in endpoints):endpoint('primary',fallback_primary)
                    for instance in connection.instance_endpoints or []:
                        endpoint('instance',getattr(instance.endpoint,'ip_address',None),instance.db_instance_id)
                else:endpoint('primary',fallback_primary)
            else:
                subnet=observed('subnet_id');nsgs=[observed('nsg_id')] if observed('nsg_id') else []
                endpoint('search',observed('opensearch_private_ip'))
                endpoint('dashboard',observed('opendashboard_private_ip'))
            endpoints.sort(key=lambda e:(e['role'] not in ('primary','search'),e['role'],e['ip_address'],e.get('instance_id','')))
            ips=list(dict.fromkeys(e['ip_address'] for e in endpoints))
            data={'subnet_id':subnet,'nsg_ids':nsgs,'private_ips':ips,'endpoints':endpoints,
                  'primary_private_ip':ips[0] if ips else None,
                  'detail_status':'ok' if detail is not None else 'unavailable',
                  'network_status':'ok' if subnet else ('unavailable' if detail is None else 'not_reported'),
                  'lifecycle_state':observed('lifecycle_state')}
            if service=='opensearch' and observed('vcn_id'):data['vcn_id']=observed('vcn_id')
            add(summary,kind,**data)

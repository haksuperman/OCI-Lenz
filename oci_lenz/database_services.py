"""Scoped database infrastructure metadata; never serialize SDK response objects."""

# The exact response model and reference fields define canonical graph evidence.
MODELS={
    'mysql_db_system':'DbSystem',
    'autonomous_database':'AutonomousDatabase',
    'autonomous_container_database':'AutonomousContainerDatabase',
    'autonomous_exadata_infrastructure':'AutonomousExadataInfrastructure',
    'autonomous_vm_cluster':'AutonomousVmCluster',
    'cloud_autonomous_vm_cluster':'CloudAutonomousVmCluster',
    'exadata_infrastructure':'ExadataInfrastructure',
    'vm_cluster':'VmCluster',
    'vm_cluster_network':'VmClusterNetwork',
    'cloud_exadata_infrastructure':'CloudExadataInfrastructure',
    'cloud_vm_cluster':'CloudVmCluster',
    'exadata_db_system':'DbSystem',
    'exascale_db_storage_vault':'ExascaleDbStorageVault',
    'exadb_vm_cluster':'ExadbVmCluster',
}
REFERENCES=('autonomous_container_database_id','autonomous_exadata_infrastructure_id',
    'autonomous_vm_cluster_id','cloud_autonomous_vm_cluster_id',
    'exadata_infrastructure_id','cloud_exadata_infrastructure_id',
    'vm_cluster_network_id','exascale_db_storage_vault_id')
CLUSTERS=('vm_cluster','cloud_vm_cluster','exadb_vm_cluster','exadata_db_system')
DB_SYSTEMS=('db_system',*CLUSTERS)


def node_owner(node):
    return node.get('vm_cluster_id') or node.get('db_system_id')


def fields(obj,names):
    return {name:getattr(obj,name,None) for name in names}


def store(add,obj,kind,**extra):
    data=fields(obj,('lifecycle_state','shape','node_count','subnet_id','backup_subnet_id',*REFERENCES))
    data['nsg_ids']=getattr(obj,'nsg_ids',None) or []
    data['backup_nsg_ids']=getattr(obj,'backup_network_nsg_ids',None) or []
    data.update(extra)
    add(obj,kind,**data)


def collect_mysql(call,add,compartment):
    for summary in call('mysql','list_db_systems',compartment_id=compartment) or []:
        detail=call('mysql','get_db_system',summary.id)
        obj=detail or summary
        # Retain summary IPs even when the detail request fails or omits endpoints.
        endpoints=getattr(obj,'endpoints',None) or getattr(summary,'endpoints',None) or []
        addresses={e.ip_address for e in endpoints if e.ip_address}
        if getattr(obj,'ip_address',None):addresses.add(obj.ip_address)
        store(add,summary,'mysql_db_system',**fields(obj,('subnet_id','port','port_x','mysql_version','shape_name','is_highly_available','is_heat_wave_cluster_attached')),
            nsg_ids=getattr(obj,'nsg_ids',None) or [],private_ips=sorted(addresses),
            endpoints=[fields(e,('ip_address','port','port_x')) for e in endpoints])


def collect_autonomous(call,add,compartment):
    for obj in call('database','list_autonomous_databases',compartment_id=compartment) or []:
        ip=getattr(obj,'private_endpoint_ip',None)
        store(add,obj,'autonomous_database',private_ips=[ip] if ip else [],
            **fields(obj,('db_workload','db_version','is_dedicated','infrastructure_type')))
    for api,kind in (
        ('list_autonomous_container_databases','autonomous_container_database'),
        ('list_autonomous_exadata_infrastructures','autonomous_exadata_infrastructure'),
        ('list_autonomous_vm_clusters','autonomous_vm_cluster'),
        ('list_cloud_autonomous_vm_clusters','cloud_autonomous_vm_cluster')):
        for obj in call('database',api,compartment_id=compartment) or []:store(add,obj,kind)


def collect_cluster_nodes(call,add,snapshot,compartment,cluster,filter_name='vm_cluster_id'):
    from .database import collect_nodes
    collect_nodes(call,add,snapshot,compartment,cluster,filter_name)


def collect_exacc(call,add,snapshot,compartment):
    infrastructure_ids=set()
    for obj in call('database','list_exadata_infrastructures',compartment_id=compartment) or []:
        store(add,obj,'exadata_infrastructure');infrastructure_ids.add(obj.id)
    for obj in call('database','list_vm_clusters',compartment_id=compartment) or []:
        store(add,obj,'vm_cluster')
        collect_cluster_nodes(call,add,snapshot,compartment,obj)
    # An infrastructure may be in another compartment while its VM network is
    # in this one. The explicit compartment filter remains on every network list.
    infrastructure_ids.update(r['exadata_infrastructure_id'] for r in snapshot['resources']
        if r['kind'] in ('vm_cluster','autonomous_vm_cluster') and r.get('exadata_infrastructure_id'))
    for key in sorted(infrastructure_ids):
        for network in call('database','list_vm_cluster_networks',exadata_infrastructure_id=key,compartment_id=compartment) or []:
            networks=[]
            for net in network.vm_networks or []:
                networks.append({'network_type':net.network_type,
                    'nodes':[fields(n,('ip','vip')) for n in net.nodes or []]})
            store(add,network,'vm_cluster_network',vm_networks=networks,
                scans=[{'ips':scan.ips or []} for scan in network.scans or []])


def collect_cloud_cluster(call,add,snapshot,compartment,obj,kind):
    # SCAN references are PrivateIp OCIDs, not IP strings or VNIC IDs.
    addresses=set();scan_addresses=[]
    for key in getattr(obj,'scan_ip_ids',None) or []:
        ip=call('network','get_private_ip',key)
        if ip is not None and ip.ip_address:
            addresses.add(ip.ip_address);scan_addresses.append({'private_ip_id':key,'ip_address':ip.ip_address})
    store(add,obj,kind,scan_ip_ids=getattr(obj,'scan_ip_ids',None) or [],private_ips=sorted(addresses),scan_ip_addresses=scan_addresses)
    collect_cluster_nodes(call,add,snapshot,compartment,obj)


def collect_exaci(call,add,snapshot,compartment):
    for obj in call('database','list_cloud_exadata_infrastructures',compartment_id=compartment) or []:
        store(add,obj,'cloud_exadata_infrastructure')
    for obj in call('database','list_cloud_vm_clusters',compartment_id=compartment) or []:
        collect_cloud_cluster(call,add,snapshot,compartment,obj,'cloud_vm_cluster')


def collect_exascale(call,add,snapshot,compartment):
    for obj in call('database','list_exascale_db_storage_vaults',compartment_id=compartment) or []:
        store(add,obj,'exascale_db_storage_vault')
    for obj in call('database','list_exadb_vm_clusters',compartment_id=compartment) or []:
        collect_cloud_cluster(call,add,snapshot,compartment,obj,'exadb_vm_cluster')

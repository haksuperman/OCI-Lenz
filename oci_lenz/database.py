"""Oracle DB nodes and their networks; no SQL access or credential payloads."""


def collect_nodes(call,add,snapshot,compartment,system,filter_name='db_system_id'):
    resources={r['id']:r for r in snapshot['resources']}
    for node in call('database','list_db_nodes',compartment_id=compartment,**{filter_name:system.id}) or []:
        refs={field:getattr(node,field,None) for field in ('vnic_id','vnic2_id','backup_vnic_id','backup_vnic2_id')}
        owner=getattr(node,'db_system_id',None) if filter_name=='db_system_id' else None
        evidence='DbNode.db_system_id' if owner else 'ListDbNodes.'+filter_name+' request filter'
        add(node,'db_node',**{filter_name:owner or system.id},db_system_evidence=evidence,**refs)
        stored=snapshot['resources'][-1]
        stored['name']=node.hostname or 'DB Node'
        stored.setdefault('compartment_id',getattr(system,'compartment_id',None) or compartment)
        for field,vnic_id in refs.items():
            if not vnic_id:continue
            if vnic_id in resources:
                resources[vnic_id]['db_node_id']=node.id
                continue
            vnic=call('network','get_vnic',vnic_id)
            if vnic is None:continue
            subnet=resources.get(vnic.subnet_id,{})
            ips=call('network','list_private_ips',vnic_id=vnic.id)
            private_ips={p.ip_address for p in ips or [] if p.ip_address}
            if vnic.private_ip:private_ips.add(vnic.private_ip)
            add(vnic,'vnic',db_node_id=node.id,subnet_id=vnic.subnet_id,vcn_id=subnet.get('vcn_id'),
                nsg_ids=vnic.nsg_ids or [],private_ips=sorted(private_ips),
                primary_private_ip=vnic.private_ip,public_ip=getattr(vnic,'public_ip',None),
                network_role='backup' if field.startswith('backup_') else 'client')
            resources[vnic.id]=snapshot['resources'][-1]


def collect_base_database(call,add,snapshot,compartment):
    for system in call('database','list_db_systems',compartment_id=compartment) or []:
        shape=getattr(system,'shape',None) or ''
        # Legacy Exadata DbSystems still use the DbSystem API, unlike current CloudVmClusters.
        kind='exadata_db_system' if shape.startswith('Exadata.') else 'db_system'
        if not shape.startswith(('VM.','BM.','Exadata.')):
            snapshot['coverage'].append({'region':snapshot['scope']['region'],'compartment':compartment,
                'service':'database','resource_type':'db_system_shape','shape':shape or 'UNKNOWN','status':'unsupported'})
            continue
        add(system,kind,subnet_id=system.subnet_id,backup_subnet_id=system.backup_subnet_id,
            nsg_ids=system.nsg_ids or [],backup_nsg_ids=system.backup_network_nsg_ids or [],
            shape=shape,node_count=system.node_count,version=system.version)
        collect_nodes(call,add,snapshot,compartment,system)

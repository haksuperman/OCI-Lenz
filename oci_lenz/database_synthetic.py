"""Independent, explicitly synthetic database service examples."""

CASES=('mysql','autonomous-db','exacc','exaci','exascale')


def add_database_scenario(snapshot,case):
    resources=snapshot['resources']
    def add(key,kind,name,**fields):
        resources.append(dict(id=key,kind=kind,name='Synthetic '+name,compartment_id='synthetic-compartment-1',**fields))
    if case=='mysql':
        add('qa-mysql','mysql_db_system','MySQL',subnet_id='private',nsg_ids=['app-nsg'],private_ips=['10.0.1.61'],mysql_version='8.4',port=3306)
        next(r for r in resources if r['kind']=='backend_set')['backends']=[{'ip_address':'10.0.1.61','port':3306}]
    elif case=='autonomous-db':
        add('qa-adb','autonomous_database','Private Autonomous DB',subnet_id='private',nsg_ids=['app-nsg'],private_ips=['10.0.1.61'],autonomous_container_database_id='qa-acd',is_dedicated=True)
        add('qa-public-adb','autonomous_database','Public Autonomous DB',is_dedicated=False)
        add('qa-acd','autonomous_container_database','Autonomous Container DB',cloud_autonomous_vm_cluster_id='qa-acvm')
        add('qa-acvm','cloud_autonomous_vm_cluster','Autonomous VM Cluster',subnet_id='private',cloud_exadata_infrastructure_id='qa-adb-infra')
        add('qa-adb-infra','cloud_exadata_infrastructure','Autonomous Cloud Infrastructure')
    else:
        key='qa-'+case+'-cluster'
        if case=='exacc':
            add('qa-cc-infra','exadata_infrastructure','ExaCC Infrastructure')
            add('qa-cc-network','vm_cluster_network','ExaCC VM Network',exadata_infrastructure_id='qa-cc-infra',vm_networks=[{'network_type':'CLIENT','nodes':[{'ip':'10.0.1.61'},{'ip':'10.0.1.62'}]},{'network_type':'BACKUP','nodes':[{'ip':'10.9.0.61'}]}])
            add(key,'vm_cluster','ExaCC VM Cluster',exadata_infrastructure_id='qa-cc-infra',vm_cluster_network_id='qa-cc-network')
            # These addresses belong to the physical client network, not an OCI subnet.
            return
        if case=='exaci':
            add('qa-ci-infra','cloud_exadata_infrastructure','ExaCI Infrastructure')
            refs={'cloud_exadata_infrastructure_id':'qa-ci-infra'};kind='cloud_vm_cluster'
        else:
            add('qa-xs-vault','exascale_db_storage_vault','Exascale Storage Vault')
            refs={'exascale_db_storage_vault_id':'qa-xs-vault'};kind='exadb_vm_cluster'
        add(key,kind,case+' VM Cluster',subnet_id='private',nsg_ids=['app-nsg'],**refs)
        for i in range(2):
            node=key+'-node-'+str(i);vnic=node+'-vnic'
            add(node,'db_node',case+' internal node '+str(i),vm_cluster_id=key,vnic_id=vnic,db_system_evidence='ListDbNodes.vm_cluster_id request filter')
            add(vnic,'vnic',case+' client VNIC '+str(i),db_node_id=node,subnet_id='private',vcn_id='vcn',private_ips=['10.0.1.'+str(61+i)],network_role='client')
        # Explicit configured backend evidence to a collected Node IP.
        next(r for r in resources if r['kind']=='backend_set')['backends']=[{'ip_address':'10.0.1.61','port':1521}]

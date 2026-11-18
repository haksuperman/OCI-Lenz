"""Minimal snapshots and evidence-based relationships. Never stores SDK objects."""

def sample(scenario='basic'):
    result=_sample(scenario)
    result['scope']['tenancy_name']='Synthetic Tenancy'
    result['scope']['compartment_names']={key:'Synthetic Compartment '+str(i+1) for i,key in enumerate(result['scope']['compartments'])}
    return result


def _sample(scenario):
    from .synthetic import SCENARIOS,build_scenario
    if scenario in SCENARIOS:return build_scenario(scenario)
    if scenario == 'service-map':
        import copy
        resources=[]
        groups=[{'label':'Service A','vcn_ids':['s1-vcn','s2-vcn']},
                {'label':'Service B','vcn_ids':['s3-vcn']},
                {'label':'Service C','vcn_ids':['s4-vcn']},
                {'label':'Shared services','role':'shared','vcn_ids':['s5-vcn']}]
        for i in range(1,6):
            prefix=f's{i}-'; base=copy.deepcopy(sample()['resources'])
            # Independent synthetic topology: each LB has two uniquely resolved backends.
            base.append(dict(base[-2],id='compute-2',name='Compute 2'))
            base.append(dict(base[-2],id='vnic-2',name='VNIC 2',kind='vnic',
                             instance_id='compute-2',subnet_id='private',vcn_id='vcn',
                             private_ips=['10.0.1.11'],nsg_ids=['app-nsg']))
            next(r for r in base if r['kind']=='backend_set')['backends'].append({'ip_address':'10.0.1.11','port':8080})
            for r in base:
                r['id']=prefix+r['id'];r['name']=prefix+r['name']
                r['compartment_id']='synthetic-compartment-'+str(min(i,4))
                for field in ('vcn_id','subnet_id','route_table_id','instance_id','lb_id'):
                    if r.get(field):r[field]=prefix+r[field]
                for field in ('subnet_ids','nsg_ids'):
                    if field in r:r[field]=[prefix+k for k in r[field]]
                for rule in r.get('rules',[]):rule['network_entity_id']=prefix+rule['network_entity_id']
                resources.append(r)
        counts={}
        for r in resources:
            key=(r['compartment_id'],r['kind']);counts[key]=counts.get(key,0)+1
        return {'version':1,'scope':{'region':'sample-region','compartments':sorted({r['compartment_id'] for r in resources})},
                'presentation':{'groups':groups},'resources':resources,
                'coverage':[{'region':'sample-region','compartment':c,'service':k,'status':'ok','count':n,'source':'synthetic'} for (c,k),n in sorted(counts.items())]}
    if scenario == 'overview':
        import copy
        resources=[]
        for i in range(3):
            prefix=f'demo-{i+1}-'
            comp='synthetic-compartment-'+str(1 if i<2 else 2)
            for original in sample()['resources']:
                r=copy.deepcopy(original);r['id']=prefix+r['id'];r['name']=prefix+r['name']
                r['compartment_id']=comp
                for field in ('vcn_id','subnet_id','route_table_id','instance_id','lb_id'):
                    if r.get(field): r[field]=prefix+r[field]
                for field in ('subnet_ids','nsg_ids'):
                    if field in r: r[field]=[prefix+k for k in r[field]]
                for rule in r.get('rules',[]): rule['network_entity_id']=prefix+rule['network_entity_id']
                resources.append(r)
        counts={}
        for r in resources:
            key=(r['compartment_id'],r['kind']);counts[key]=counts.get(key,0)+1
        return {'version':1,'scope':{'region':'sample-region','compartments':['synthetic-compartment-1','synthetic-compartment-2']},
                'resources':resources,'coverage':[{'region':'sample-region','compartment':c,'service':k,'status':'ok','count':n,'source':'synthetic'} for (c,k),n in sorted(counts.items())]}
    if scenario != 'basic': raise ValueError('unsupported synthetic scenario')
    def r(id, kind, **fields): return dict(id=id,kind=kind,name=id.replace('-',' ').title(),**fields)
    return {'version':1,'scope':{'region':'sample-region','compartments':['sample']},'coverage':[{'region':'sample-region','compartment':'sample','service':kind,'status':'ok','count':count,'source':'synthetic'} for kind,count in [('vcn',1),('subnet',2),('compute',1),('lb',1),('gateways',3),('nsg',1),('route',2)]], 'resources':[
        r('vcn','vcn'), r('public','subnet',vcn_id='vcn',public=True,route_table_id='public-rt'),
        r('private','subnet',vcn_id='vcn',public=False,route_table_id='private-rt'),
        r('nat','nat',vcn_id='vcn'),r('internet','internet',vcn_id='vcn'),r('service','service',vcn_id='vcn'),
        r('app-nsg','nsg',vcn_id='vcn'),r('private-rt','route',vcn_id='vcn',rules=[{'destination':'0.0.0.0/0','network_entity_id':'nat'}]),
        r('public-rt','route',vcn_id='vcn',rules=[{'destination':'0.0.0.0/0','network_entity_id':'internet'}]),
        r('lb','lb',subnet_ids=['public'],nsg_ids=['app-nsg'],ip_addresses=[{'ip_address':'192.0.2.20','is_public':True}]),
        r('backend-set','backend_set',lb_id='lb',backends=[{'ip_address':'10.0.1.10','port':8080}]),
        r('compute','compute'),r('vnic','vnic',instance_id='compute',subnet_id='private',vcn_id='vcn',private_ips=['10.0.1.10'],nsg_ids=['app-nsg'])]}


def graph(snapshot):
    resources = snapshot['resources']
    nodes={r['id']:dict(r) for r in resources}
    if len(nodes)!=len(resources): raise ValueError('duplicate resource IDs')
    edges=[]
    def edge(source,target,kind,evidence,label=''):
        if target not in nodes:
            unknown='unknown:'+target
            nodes.setdefault(unknown,{'id':unknown,'kind':'unknown','name':'대상 미확인'})
            target=unknown
        edges.append(dict(source=source,target=target,kind=kind,evidence=evidence,label=label))
    for r in resources:
        rid=r['id']; kind=r['kind']
        for field in ('vcn_id','subnet_id','route_table_id','instance_id','lb_id'):
            if r.get(field): edge(rid,r[field],field,field)
        for field in ('subnet_ids','nsg_ids'):
            for target in r.get(field,[]): edge(rid,target,field,field)
        if kind=='db_system':
            if r.get('backup_subnet_id'):edge(rid,r['backup_subnet_id'],'backup_subnet_id','DbSystem.backup_subnet_id')
            for target in r.get('backup_nsg_ids',[]):edge(rid,target,'backup_nsg_ids','DbSystem.backup_network_nsg_ids[]')
        if kind=='db_node':
            if r.get('db_system_id'):edge(rid,r['db_system_id'],'db_system_id',r.get('db_system_evidence') or 'DbNode.db_system_id')
            for field in ('vnic_id','vnic2_id','backup_vnic_id','backup_vnic2_id'):
                if r.get(field):edge(rid,r[field],field,'DbNode.'+field)
        if kind in ('drg_attachment','rpc','ipsec') and r.get('drg_id'):
            edge(rid,r['drg_id'],'drg_id',{'drg_attachment':'DrgAttachment','rpc':'RemotePeeringConnection','ipsec':'IPSecConnection'}[kind]+'.drg_id')
        if kind=='virtual_circuit':
            if r.get('gateway_id'):edge(rid,r['gateway_id'],'gateway_id','VirtualCircuit.gateway_id')
            targets=set()
            for i,mapping in enumerate(r.get('cross_connect_mappings',[])):
                target=mapping.get('cross_connect_or_cross_connect_group_id') or 'missing-cross-connect:'+rid+':'+str(i)
                if target not in targets:edge(rid,target,'cross_connect_mapping','VirtualCircuit.cross_connect_mappings[].cross_connect_or_cross_connect_group_id')
                targets.add(target)
        if kind=='cross_connect' and r.get('cross_connect_group_id'):
            edge(rid,r['cross_connect_group_id'],'cross_connect_group_id','CrossConnect.cross_connect_group_id')
        if kind=='ipsec' and r.get('cpe_id'):
            edge(rid,r['cpe_id'],'cpe_id','IPSecConnection.cpe_id')
        if kind=='ipsec_tunnel' and r.get('ipsec_id'):
            edge(rid,r['ipsec_id'],'ipsec_id','ListIPSecConnectionTunnels.ipsc_id (request scope)')
        if kind=='drg_attachment':
            edge(rid,r.get('network_id') or 'missing-attachment-network:'+rid,'attachment_network',r.get('network_evidence') or 'DrgAttachment.network_details.id')
        if kind in ('lpg','rpc'):
            evidence=('LocalPeeringGateway' if kind=='lpg' else 'RemotePeeringConnection')+'.peer_id'
            if r.get('peer_id'):edge(rid,r['peer_id'],'peer_id',evidence)
            elif r.get('peering_status')=='PEERED':edge(rid,'peer:'+rid,'peer_id',evidence+' unavailable; peering_status=PEERED')
        if kind=='subnet':
            rt=nodes.get(r.get('route_table_id'),{})
            for rule in rt.get('rules',[]):
                edge(rid,rule.get('network_entity_id','missing'),'route',
                     'Subnet.route_table_id → RouteTable.route_rules[].network_entity_id',rule.get('destination',''))
        if kind=='backend_set':
            lb=nodes.get(r.get('lb_id'),{})
            vcns={nodes.get(s,{}).get('vcn_id') for s in lb.get('subnet_ids',[])}-{None}
            for backend in r.get('backends',[]):
                matches=[n for n in resources if n['kind']=='vnic' and (n.get('vcn_id') or nodes.get(n.get('subnet_id'),{}).get('vcn_id')) in vcns and backend['ip_address'] in n.get('private_ips',[])]
                target=(matches[0].get('instance_id') or matches[0].get('db_node_id') or matches[0]['id']) if len(matches)==1 else 'backend:'+rid+':'+str(len(edges))
                edge(rid,target,'backend','BackendSet.backends[].ip_address → unique VNIC/PrivateIp in LB VCN',f"Backend :{backend['port']}")
    return nodes,edges

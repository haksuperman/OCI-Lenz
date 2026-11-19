"""Independent synthetic inventories for repeatable topology/label validation."""
import copy
from collections import Counter

from .database_synthetic import CASES as DATABASE_CASES

SCENARIOS=('regional-waf','network-load-balancer','long-names','dense','fanout','cross-compartment','unresolved','empty','network-peering','base-database','ipsec-vpn','drg-centered','fastconnect',*DATABASE_CASES)


def build_scenario(case):
    from .model import sample
    if case not in SCENARIOS:raise ValueError('unknown synthetic matrix case')
    s=sample('overview' if case in ('cross-compartment','network-peering') else 'basic')
    if case=='regional-waf':
        s['resources'].append({'id':'synthetic-waf','kind':'waf','name':'Synthetic Regional WAF',
            'compartment_id':'synthetic-compartment-1','backend_type':'LOAD_BALANCER',
            'load_balancer_id':'lb','web_app_firewall_policy_id':'synthetic-waf-policy'})
    elif case=='network-load-balancer':
        lb=next(r for r in s['resources'] if r['kind']=='lb')
        lb.update(kind='nlb',name='Synthetic Network Load Balancer',subnet_id='public')
        lb.pop('subnet_ids')
        lb['ip_addresses']=[{'ip_address':'192.0.2.30','is_public':True}]
        backend=next(r for r in s['resources'] if r['kind']=='backend_set')
        backend['backends'][0]['target_id']='compute'
        vnic=next(r for r in s['resources'] if r['kind']=='vnic')
        vnic['private_ip_ids']=['synthetic-private-ip']
        s['resources'].append({'id':'synthetic-private-nlb','kind':'nlb','name':'Synthetic Private NLB',
            'compartment_id':'synthetic-compartment-1','subnet_id':'private','nsg_ids':['app-nsg'],
            'ip_addresses':[{'ip_address':'10.0.1.30','is_public':False}]})
        s['resources'].append({'id':'synthetic-private-nlb/backend-set/servers','kind':'backend_set',
            'name':'Synthetic private targets','lb_id':'synthetic-private-nlb',
            'backends':[{'target_id':'synthetic-private-ip','ip_address':None,'port':443}]})
    elif case in DATABASE_CASES:
        from .database_synthetic import add_database_scenario
        add_database_scenario(s,case)
    elif case=='empty':s['resources']=[]
    elif case=='long-names':
        for r in s['resources']:
            r['name']='가상검증용 긴 이름 - Synthetic-Architecture-Validation-'+r['kind']+'-'+r['id']
        next(r for r in s['resources'] if r['id']=='private')['name']='가상검증용 응용 네트워크 경계 - Synthetic-Network-Title-'*3
    elif case in ('dense','fanout'):
        base={r['id']:r for r in s['resources']}
        count=24 if case=='dense' else 8
        for i in range(1,count):
            vm=copy.deepcopy(base['compute']);vm.update(id=f'qa-vm-{i:02}',name=f'Synthetic application node {i:02}')
            nic=copy.deepcopy(base['vnic']);nic.update(id=f'qa-nic-{i:02}',name=f'Synthetic NIC {i:02}',instance_id=vm['id'],private_ips=[f'10.0.1.{10+i}'])
            s['resources'].extend((vm,nic))
        sets=[base['backend-set']]
        if case=='fanout':
            for i in range(1,3):
                bs=copy.deepcopy(base['backend-set']);bs.update(id=f'qa-set-{i}',name=f'Synthetic backend set {i}',backends=[])
                s['resources'].append(bs);sets.append(bs)
        for bs in sets:bs['backends']=[]
        for i in range(count):sets[i%len(sets)]['backends'].append({'ip_address':f'10.0.1.{10+i}','port':8080})
        if case=='dense':
            for i in range(4):s['resources'].append({'id':f'qa-empty-subnet-{i}','name':f'Synthetic empty subnet {i}','kind':'subnet','vcn_id':'vcn','public':False})
    elif case=='cross-compartment':
        # An instance has its primary network in another compartment plus a
        # secondary VNIC in a second VCN. LB spans two observed subnets.
        vm=next(r for r in s['resources'] if r['id']=='demo-1-compute');vm['compartment_id']='synthetic-compartment-2'
        nic=next(r for r in s['resources'] if r['id']=='demo-1-vnic');nic['is_primary']=True
        secondary=copy.deepcopy(nic);secondary.update(id='qa-secondary',name='Synthetic secondary NIC',is_primary=False,subnet_id='demo-3-private',vcn_id='demo-3-vcn',private_ips=['10.0.3.99'],compartment_id='synthetic-compartment-2')
        s['resources'].append(secondary)
        lb=next(r for r in s['resources'] if r['id']=='demo-1-lb');lb['subnet_ids'].append('demo-1-private')
    elif case=='network-peering':
        s['resources'].extend([
            {'id':'qa-drg','kind':'drg','name':'Synthetic shared DRG','compartment_id':'synthetic-compartment-1'},
            {'id':'qa-attach-a','kind':'drg_attachment','name':'Synthetic attachment A','drg_id':'qa-drg','network_id':'demo-1-vcn','network_type':'VCN'},
            {'id':'qa-attach-b','kind':'drg_attachment','name':'Synthetic attachment B','drg_id':'qa-drg','network_id':'demo-3-vcn','network_type':'VCN','compartment_id':'synthetic-compartment-2'},
            {'id':'qa-lpg-a','kind':'lpg','name':'Synthetic local peer A','vcn_id':'demo-1-vcn','peer_id':'qa-lpg-b','peering_status':'PEERED'},
            {'id':'qa-lpg-b','kind':'lpg','name':'Synthetic local peer B','vcn_id':'demo-3-vcn','peer_id':'qa-lpg-a','peering_status':'PEERED','compartment_id':'synthetic-compartment-2'},
            {'id':'qa-rpc','kind':'rpc','name':'Synthetic remote peer','drg_id':'qa-drg','peer_id':'qa-outside-rpc','peer_region_name':'other-synthetic-region','peering_status':'PEERED'}])
    elif case=='fastconnect':
        s=sample('drg-centered')
        s['resources'].extend([
            {'id':'qa-fc','kind':'virtual_circuit','name':'Synthetic private FastConnect','gateway_id':'qa-drg','circuit_type':'PRIVATE','bandwidth_shape_name':'1 Gbps','bgp_session_state':'UP','cross_connect_mappings':[{'cross_connect_or_cross_connect_group_id':'qa-cross-group','customer_bgp_peering_ip':'192.0.2.0/31','oracle_bgp_peering_ip':'192.0.2.1/31','vlan':100}]},
            {'id':'qa-fc-attach','kind':'drg_attachment','name':'Internal synthetic circuit attachment','drg_id':'qa-drg','network_id':'qa-fc','network_type':'VIRTUAL_CIRCUIT'},
            {'id':'qa-cross-group','kind':'cross_connect_group','name':'Synthetic physical link group'},
            {'id':'qa-cross-connect','kind':'cross_connect','name':'Synthetic physical port','cross_connect_group_id':'qa-cross-group','port_speed_shape_name':'10 Gbps'},
            {'id':'qa-public-fc','kind':'virtual_circuit','name':'Synthetic public FastConnect','circuit_type':'PUBLIC','cross_connect_mappings':[]}])
    elif case=='drg-centered':
        s=sample('ipsec-vpn')
        s['resources'].extend([
            {'id':'remote','kind':'rpc','name':'Synthetic remote peering','drg_id':'qa-drg','peer_id':'outside'},
            {'id':'remote-attach','kind':'drg_attachment','name':'Synthetic remote attachment','drg_id':'qa-drg','network_id':'remote','network_type':'REMOTE_PEERING_CONNECTION'}])
    elif case=='ipsec-vpn':
        s['resources'].extend([
            {'id':'qa-drg','kind':'drg','name':'Synthetic VPN DRG'},
            {'id':'qa-vcn-attach','kind':'drg_attachment','name':'Synthetic VCN attachment','drg_id':'qa-drg','network_id':'vcn','network_type':'VCN'},
            {'id':'qa-cpe','kind':'cpe','name':'Synthetic premises router','ip_addresses':['192.0.2.10']},
            {'id':'qa-vpn','kind':'ipsec','name':'Synthetic site-to-site VPN','cpe_id':'qa-cpe','drg_id':'qa-drg','static_routes':['10.20.0.0/16']}])
        for i in range(2):
            tunnel='qa-tunnel-'+str(i)
            s['resources'].extend([
                {'id':tunnel,'kind':'ipsec_tunnel','name':'Synthetic tunnel '+str(i+1),'ipsec_id':'qa-vpn','ip_addresses':['198.51.100.'+str(10+i)],'cpe_ip':'192.0.2.10','status':'UP' if i==0 else 'DOWN','routing':'BGP' if i==0 else 'STATIC'},
                {'id':'qa-tunnel-attach-'+str(i),'kind':'drg_attachment','name':'Synthetic tunnel attachment '+str(i+1),'drg_id':'qa-drg','network_id':tunnel,'network_type':'IPSEC_TUNNEL'}])
    elif case=='base-database':
        s['resources'].extend([
            {'id':'db-backup-subnet','name':'Synthetic backup subnet','kind':'subnet','vcn_id':'vcn','cidr_block':'10.0.2.0/24','public':False},
            {'id':'qa-base-db','name':'Synthetic Oracle Base DB','kind':'db_system','shape':'VM.BaseDB.x86','subnet_id':'private','backup_subnet_id':'db-backup-subnet','nsg_ids':['app-nsg']},
            {'id':'qa-db-set','name':'Synthetic database targets','kind':'backend_set','lb_id':'lb','backends':[{'ip_address':'10.0.1.20','port':1521}]}])
        for i in range(2):
            node='qa-db-node-'+str(i);client='qa-db-client-'+str(i);backup='qa-db-backup-'+str(i)
            s['resources'].append({'id':node,'name':'Internal synthetic DB hostname '+str(i),'kind':'db_node','db_system_id':'qa-base-db','vnic_id':client,'backup_vnic_id':backup})
            for key,subnet,role,address in ((client,'private','client','10.0.1.'+str(20+i)),(backup,'db-backup-subnet','backup','10.0.2.'+str(20+i))):
                s['resources'].append({'id':key,'name':'Synthetic DB '+role+' VNIC '+str(i),'kind':'vnic','db_node_id':node,'subnet_id':subnet,'vcn_id':'vcn','private_ips':[address],'primary_private_ip':address,'network_role':role})
    elif case=='unresolved':
        s['resources']=[r for r in s['resources'] if r['id'] not in ('nat','vcn')]
        bs=next(r for r in s['resources'] if r['kind']=='backend_set')
        bs['backends'].append({'ip_address':'192.0.2.99','port':8443})
        s['resources'].append({'id':'qa-unattached-vm','kind':'compute','name':'Synthetic instance without observed VNIC'})
    for r in s['resources']:r.setdefault('compartment_id','synthetic-compartment-1')
    s['scope']={'region':'sample-region','compartments':sorted({r['compartment_id'] for r in s['resources']}) or ['synthetic-compartment-1']}
    counts=Counter((r['compartment_id'],r['kind']) for r in s['resources'])
    s['coverage']=[{'region':'sample-region','compartment':c,'service':k,'count':n,'status':'ok','source':'synthetic'} for (c,k),n in sorted(counts.items())]
    if not s['coverage']:s['coverage']=[{'region':'sample-region','compartment':'synthetic-compartment-1','service':'inventory','count':0,'status':'ok','source':'synthetic'}]
    return s

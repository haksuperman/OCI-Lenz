"""Independent synthetic inventories for repeatable topology/label validation."""
import copy
from collections import Counter

SCENARIOS=('long-names','dense','fanout','cross-compartment','unresolved','empty')


def build_scenario(case):
    from .model import sample
    if case not in SCENARIOS:raise ValueError('unknown synthetic matrix case')
    s=sample('overview' if case=='cross-compartment' else 'basic')
    if case=='empty':s['resources']=[]
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

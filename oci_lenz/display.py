"""Local operational labels; optional redaction is for sharing only."""
import copy
import textwrap
from .model import graph


def scope_title(snapshot):
    scope=snapshot['scope'];redacted=snapshot.get('presentation',{}).get('redacted')
    tenancy='Hidden' if redacted else scope.get('tenancy_name') or '이름 미확인'
    names=scope.get('compartment_names',{})
    compartments=[('Compartment '+str(i+1)) if redacted else names.get(key) or ('이름 미확인 ('+str(i+1)+')')
                  for i,key in enumerate(scope.get('compartments',[]))]
    return 'Tenancy: '+tenancy+'\nCompartment: '+(', '.join(compartments) or '이름 미확인')+' | Region: '+scope['region']


def resource_label(resource,width=22):
    lines=[resource['name'],*resource.get('display_details',[])]
    return '\n'.join(part for line in lines for part in (textwrap.wrap(line,width=width,break_long_words=True,break_on_hyphens=False) or ['']))


def network_label(resource,prefix):
    lines=[prefix+resource['name']]
    lines.extend(resource.get('display_details',[]))
    return '\n'.join(part for line in lines for part in (textwrap.wrap(line,width=44,break_on_hyphens=False) or ['']))


def prepare_display(snapshot,redact=False):
    result=copy.deepcopy(snapshot)
    result.setdefault('presentation',{})['redacted']=redact
    from .database_services import DB_SYSTEMS,node_owner,MODELS
    nodes,_=graph(result)
    aliases={'file_system':'File System','mount_target':'Mount Target','file_export':'Export','api_gateway':'API Gateway','api_deployment':'API Deployment','functions_application':'Functions Application','function':'Function','goldengate_deployment':'OCI GoldenGate','object_storage_bucket':'Object Storage bucket','container_repository':'Container Registry','devops_project':'DevOps project','devops_repository':'Code repository','devops_build_pipeline':'Build pipeline','devops_deploy_pipeline':'Deploy pipeline','devops_deploy_environment':'Deploy environment','compute':'VM','lb':'LB','nlb':'NLB','waf':'WAF','edge_waf':'Edge WAF','edge_origin':'Origin','nosql_table':'NoSQL table','oci_cache':'OCI Cache','postgresql_db_system':'PostgreSQL','opensearch_cluster':'OpenSearch','backend_set':'Backend set','vnic':'VNIC','vcn':'VCN','subnet':'Subnet','route':'RT','nsg':'NSG','nat':'NAT','internet':'IGW','service':'SGW','drg':'DRG','lpg':'LPG','rpc':'RPC','virtual_circuit':'FastConnect','cross_connect':'CrossConnect','cross_connect_group':'CrossConnect group','cpe':'CPE','ipsec':'IPSec VPN','ipsec_tunnel':'VPN tunnel','db_system':'Base DB','db_node':'DB Node','unknown':'대상 미확인'}
    aliases.update({kind:kind.replace('_',' ').title() for kind in MODELS})
    alias={k:aliases.get(r['kind'],r['kind'])+' '+str(i+1) for i,(k,r) in enumerate(sorted(nodes.items()))}
    for r in result['resources']:
        r.pop('display_details',None)
        r.pop('summary_details',None)
        if redact:
            r['name']=alias[r['id']]
            for rule in r.get('rules',[]):
                if rule.get('destination')!='0.0.0.0/0':rule['destination']='Route destination hidden'
            continue
        details=[]
        if r['kind'] in ('oci_cache','postgresql_db_system','opensearch_cluster'):
            details.extend(["Detail collection: "+r.get('detail_status','not recorded'),"Network observation: "+r.get('network_status','not recorded')])
        sources=[r]
        if r['kind']=='compute':
            sources=[v for v in result['resources'] if v.get('instance_id')==r['id'] and v['kind']=='vnic']
        if r['kind']=='db_node':
            sources=[v for v in result['resources'] if v.get('db_node_id')==r['id'] and v['kind']=='vnic']
        if r['kind'] in DB_SYSTEMS:
            clients={n.get(field) for n in result['resources'] if n['kind']=='db_node' and node_owner(n)==r['id'] for field in ('vnic_id','vnic2_id')}-{None}
            sources=[dict(v,private_ips=([v['primary_private_ip']] if v.get('primary_private_ip') else v.get('private_ips',[])[:1])) for v in result['resources'] if v['kind']=='vnic' and v['id'] in clients]
            sources.append(r)
            network=nodes.get(r.get('vm_cluster_network_id'),{})
            client_ips=sorted({n['ip'] for net in network.get('vm_networks',[]) if net.get('network_type')=='CLIENT' for n in net.get('nodes',[]) if n.get('ip')})
            if client_ips:sources.append({'id':r['id']+'/client-network','private_ips':client_ips})
        sources=sorted(sources,key=lambda v:(v.get('network_role')=='backup',v.get('is_primary') is not True,v['id']))
        private=sorted({ip for src in sources for ip in src.get('private_ips',[]) if ip})
        public=sorted({src['public_ip'] for src in sources if src.get('public_ip')})
        details.extend('Private: '+ip for ip in private)
        details.extend('Public: '+ip for ip in public)
        preferred_private=next((src['primary_private_ip'] for src in sources if src.get('primary_private_ip')),next(iter(private),None))
        preferred_public=next((src['public_ip'] for src in sources if src.get('public_ip')),None)
        summary=[]
        if preferred_private:summary.append('Private: '+preferred_private)
        if preferred_public:summary.append('Public: '+preferred_public)
        for address in r.get('ip_addresses',[]):
            ip=address.get('ip_address') if isinstance(address,dict) else address
            if ip:
                prefix=('Public: ' if address.get('is_public') else 'Private: ') if isinstance(address,dict) else 'IP: '
                details.append(prefix+ip)
                if not any(d.startswith(prefix) for d in summary):summary.append(prefix+ip)
        cidrs=sorted(set(r.get('cidr_blocks',[]) or ([r['cidr_block']] if r.get('cidr_block') else [])))
        details.extend(cidrs)
        summary.extend(cidrs)
        for listener in r.get('listeners',[]):
            protocol=listener.get('protocol') or 'UNKNOWN'
            if listener.get('port') is None:continue
            label='Listener '+listener.get('name','')+' '+protocol+':'+str(listener['port'])
            if listener.get('default_backend_set_name'):label+=' → '+listener['default_backend_set_name']+' (default)'
            details.append(label)
        if r['kind']=='backend_set':
            details.append('Backend collection: '+r.get('backends_status','legacy status unknown'))
            details.extend(sorted({str(b.get('ip_address') or b.get('target_id') or '대상 미확인')+':'+str(b['port']) for b in r.get('backends',[])}))
        for field,label in (('peering_status','Peering status'),('peer_region_name','Peer region')):
            if r.get(field):details.append(label+': '+str(r[field]))
        for field,label in (('status','Status'),('routing','Routing'),('lifecycle_state','Lifecycle'),('cpe_ip','CPE IP')):
            if r.get(field):details.append(label+': '+str(r[field]))
        details.extend('Static route: '+route for route in r.get('static_routes',[]))
        if r['kind']=='virtual_circuit':
            peers={'Customer':[],'Oracle':[]}
            for mapping in r.get('cross_connect_mappings',[]):
                for label,field in (('Customer','customer_bgp_peering_ip'),('Oracle','oracle_bgp_peering_ip'),('Customer','customer_bgp_peering_ipv6'),('Oracle','oracle_bgp_peering_ipv6')):
                    if mapping.get(field):
                        value=label+': '+mapping[field];details.append(value);peers[label].append(value)
                if mapping.get('vlan') is not None:details.append('VLAN: '+str(mapping['vlan']))
            summary=[values[0] for values in peers.values() if values]
        for field,label in (('circuit_type','Circuit type'),('bandwidth_shape_name','Bandwidth'),('bgp_session_state','BGP IPv4 state'),('bgp_ipv6_session_state','BGP IPv6 state'),('port_speed_shape_name','Port speed'),('minimum_links','Minimum links')):
            if r.get(field) is not None:details.append(label+': '+str(r[field]))
        for field in ('mysql_version','db_version','db_workload','shape','shape_name','port','port_x','is_highly_available','is_heat_wave_cluster_attached'):
            if r.get(field) is not None:details.append(field+': '+str(r[field]))
        if r['kind']=='vm_cluster_network':
            for net in r.get('vm_networks',[]):
                details.extend(str(net.get('network_type') or 'UNKNOWN')+': '+n[field] for n in net.get('nodes',[]) for field in ('ip','vip') if n.get(field))
            details.extend('SCAN: '+ip for scan in r.get('scans',[]) for ip in scan.get('ips',[]))
        if r['kind']=='edge_waf':
            details.append('Origin status: '+r.get('origin_status','unavailable'))
            details.extend('Origin '+o['key']+': '+(o.get('host') or '대상 미확인') for o in r.get('origins',[]))
        r['display_details']=details
        r['summary_details']=['IP: '+ip for ip in private] if r['kind'] in DB_SYSTEMS else summary
    if redact:
        for i,g in enumerate(result.get('presentation',{}).get('groups',[])):
            g['label']='Shared services' if g.get('role')=='shared' else 'Service '+str(i+1)
    return result

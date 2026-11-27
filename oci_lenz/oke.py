"""Scoped OKE network metadata. No kubeconfig, Kubernetes API or invented traffic."""
from urllib.parse import urlsplit
from .managed_data import address


def endpoint_ip(value):
    ip=address(value)
    if ip:return ip
    if not isinstance(value,str):return None
    try:
        parsed=urlsplit(value if '://' in value else '//'+value)
        if parsed.username is not None or parsed.password is not None:return None
        return address(parsed.hostname)
    except ValueError:return None


def network_parent(resource,nodes):
    """An endpoint anchor is not the location of Oracle's managed control plane."""
    subnet=nodes.get(resource.get('subnet_id'),{});vcn=resource.get('vcn_id')
    if subnet.get('kind')=='subnet' and (not vcn or subnet.get('vcn_id')==vcn):return subnet['id']
    return vcn if nodes.get(vcn,{}).get('kind')=='vcn' else None


def caption_role(resource,nodes):
    return 'OKE API Endpoint' if nodes.get(network_parent(resource,nodes),{}).get('kind')=='subnet' else 'OKE Cluster'


def annotate_networks(resources):
    """Use exact returned references, also after merging selected compartments."""
    nodes={r['id']:r for r in resources}
    for cluster in resources:
        if cluster['kind']!='oke_cluster':continue
        for pool in cluster.get('node_pool_networks',[]):
            for key in pool.get('pod_subnet_ids',[]):
                r=nodes.get(key,{})
                if r.get('kind')=='subnet' and r.get('vcn_id')==cluster.get('vcn_id') and cluster.get('vcn_id'):
                    r['oke_pod_cluster_ids']=sorted(set(r.get('oke_pod_cluster_ids',[]))|{cluster['id']})
            for key in pool.get('worker_ids',[]):
                r=nodes.get(key,{})
                if r.get('kind')=='compute':r['oke_cluster_ids']=sorted(set(r.get('oke_cluster_ids',[]))|{cluster['id']})


def collect_oke(call,add,snapshot,compartment):
    def mismatch(api):
        snapshot['coverage'].append({'region':snapshot['scope']['region'],'compartment':compartment,'service':'oke',
                                     'api':api,'status':'failed','reason':'response_identity_or_scope_mismatch'})
    for summary in call('oke','list_clusters',compartment_id=compartment) or []:
        if getattr(summary,'compartment_id',None) not in (None,compartment):mismatch('list_clusters');continue
        detail=call('oke','get_cluster',cluster_id=summary.id)
        if detail is not None and (getattr(detail,'id',None)!=summary.id or getattr(detail,'compartment_id',None) not in (None,compartment)):
            mismatch('get_cluster');detail=None
        def observed(field):
            value=getattr(detail,field,None)
            return value if value is not None else getattr(summary,field,None)
        def component(field,name):
            value=getattr(getattr(detail,field,None),name,None)
            return value if value is not None else getattr(getattr(summary,field,None),name,None)
        private=endpoint_ip(component('endpoints','private_endpoint'));public=endpoint_ip(component('endpoints','public_endpoint'))
        other=sorted({ip for field in ('ipv6_endpoint','kubernetes') if (ip:=endpoint_ip(component('endpoints',field))) and ip not in (private,public)})
        def provenance(field,name=None):
            value=getattr(detail,field,None)
            if name:value=getattr(value,name,None)
            return ('Cluster' if value is not None else 'ClusterSummary')+'.'+field+('.'+name if name else '')
        evidence={'vcn_id':provenance('vcn_id'),'subnet_id':provenance('endpoint_config','subnet_id'),
                  'nsg_ids':provenance('endpoint_config','nsg_ids')+'[]'}
        pools=call('oke','list_node_pools',compartment_id=compartment,cluster_id=summary.id)
        networks=[]
        for pool in pools or []:
            if getattr(pool,'cluster_id',None)!=summary.id or getattr(pool,'compartment_id',None) not in (None,compartment):mismatch('list_node_pools');continue
            obj=call('oke','get_node_pool',node_pool_id=pool.id)
            if obj is not None and (getattr(obj,'id',None)!=pool.id or getattr(obj,'cluster_id',None)!=summary.id or getattr(obj,'compartment_id',None) not in (None,compartment)):
                # Do not promote a conflicting response to a known local pool.
                mismatch('get_node_pool');continue
            actual=obj or pool;nc=getattr(actual,'node_config_details',None)
            options=getattr(nc,'node_pool_pod_network_option_details',None)
            native=getattr(options,'cni_type',None)=='OCI_VCN_IP_NATIVE'
            pod_subnets=sorted(set(getattr(options,'pod_subnet_ids',None) or [])) if native else []
            worker_subnets=sorted({p.subnet_id for p in getattr(nc,'placement_configs',None) or [] if p.subnet_id}|set(getattr(actual,'subnet_ids',None) or []))
            worker_ids=sorted({n.id for n in getattr(actual,'nodes',None) or [] if n.id})
            networks.append({'id':pool.id,'worker_subnet_ids':worker_subnets,'pod_subnet_ids':pod_subnets,
                             'pod_nsg_ids':sorted(set(getattr(options,'pod_nsg_ids',None) or [])) if native else [],
                             'worker_ids':worker_ids,'detail_status':'ok' if obj is not None else 'unavailable',
                             'evidence':('NodePool' if obj is not None else 'NodePoolSummary')+'.node_config_details / subnet_ids / nodes[].id'})
        add(summary,'oke_cluster',compartment_id=compartment,vcn_id=observed('vcn_id'),subnet_id=component('endpoint_config','subnet_id'),
            nsg_ids=component('endpoint_config','nsg_ids') or [],private_ips=[private] if private else [],primary_private_ip=private,public_ip=public,
            ip_addresses=other,network_evidence=evidence,detail_status='ok' if detail is not None else 'unavailable',
            node_pool_status='ok' if pools is not None else 'unavailable',node_pool_networks=sorted(networks,key=lambda n:n['id']),
            lifecycle_state=observed('lifecycle_state'))
    annotate_networks(snapshot['resources'])

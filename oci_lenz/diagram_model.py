"""Evidence-based diagram projection; the collected inventory remains unchanged."""
import copy
from .model import graph


def diagram_resources(snapshot):
    return [r for r in snapshot['resources'] if r['kind']!='drg_attachment']


def diagram_graph(snapshot):
    raw,canonical=graph(snapshot)
    attachments={k for k,r in raw.items() if r['kind']=='drg_attachment'}
    nodes={k:copy.deepcopy(r) for k,r in raw.items() if k not in attachments}
    edges=[copy.deepcopy(e) for e in canonical if e['source'] not in attachments and e['target'] not in attachments]
    refs={(e['source'],e['kind']):e for e in canonical}
    for key in sorted(attachments):
        r=raw[key];owner=refs.get((key,'drg_id'));network=refs.get((key,'attachment_network'))
        source=owner['target'] if owner else 'unknown:missing-drg:'+key
        target=network['target'] if network else 'unknown:missing-network:'+key
        for endpoint in (source,target):nodes.setdefault(endpoint,{'id':endpoint,'kind':'unknown','name':'대상 미확인'})
        evidence=('DrgAttachment.drg_id' if owner else 'DrgAttachment.drg_id unavailable')+' + '+(network['evidence'] if network else 'DrgAttachment.network_details.id unavailable')
        # A native RPC owner relation already expresses the same endpoint pair.
        existing=next((e for e in edges if {e['source'],e['target']}=={source,target} and e['kind'] in ('drg_id','gateway_id','drg_network')),None)
        if existing is None:
            existing={'source':source,'target':target,'kind':'drg_network','label':'','evidence':evidence,'network_type':r.get('network_type')}
            edges.append(existing)
        elif evidence not in existing['evidence']:existing['evidence']+='; '+evidence
        existing.setdefault('attachment_ids',[]).append(key)
    for e in edges:
        if e.get('attachment_ids'):e['attachment_ids']=sorted(set(e['attachment_ids']))
    # Preserve a readable tunnel chain rather than a redundant ownership triangle.
    via_tunnels={(e['source'],nodes[e['target']].get('ipsec_id')) for e in edges if e['kind']=='drg_network' and nodes[e['target']]['kind']=='ipsec_tunnel'}
    edges=[e for e in edges if not (e['kind']=='drg_id' and nodes[e['source']]['kind']=='ipsec' and (e['target'],e['source']) in via_tunnels)]
    return nodes,edges

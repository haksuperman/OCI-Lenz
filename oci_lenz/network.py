"""Scoped DRG/peering discovery through the collector's read-only API wrapper."""


def collect_network(call,add,snapshot,compartment):
    for drg in call('network','list_drgs',compartment_id=compartment) or []:
        add(drg,'drg')
    for attachment in call('network','list_drg_attachments',compartment_id=compartment,attachment_type='ALL') or []:
        details=getattr(attachment,'network_details',None)
        network_id=getattr(details,'id',None)
        network_type=getattr(details,'type',None)
        legacy_vcn=getattr(attachment,'vcn_id',None)
        evidence='DrgAttachment.network_details.id'
        if not network_id and legacy_vcn:
            network_id=legacy_vcn;network_type='VCN';evidence='DrgAttachment.vcn_id'
        add(attachment,'drg_attachment',drg_id=attachment.drg_id,
            network_id=network_id,network_type=network_type,network_evidence=evidence)
        if network_type not in ('VCN','REMOTE_PEERING_CONNECTION','IPSEC_TUNNEL','VIRTUAL_CIRCUIT'):
            snapshot['coverage'].append({'region':snapshot['scope']['region'],'compartment':compartment,
                'service':'drg_attachment_network','resource_type':network_type or 'UNKNOWN',
                'status':'unsupported'})
    for api,kind in (('list_local_peering_gateways','lpg'),('list_remote_peering_connections','rpc')):
        for resource in call('network',api,compartment_id=compartment) or []:
            fields={'peer_id':getattr(resource,'peer_id',None),'peering_status':getattr(resource,'peering_status',None)}
            if kind=='lpg':fields['vcn_id']=resource.vcn_id
            else:fields.update(drg_id=resource.drg_id,peer_region_name=getattr(resource,'peer_region_name',None))
            add(resource,kind,**fields)

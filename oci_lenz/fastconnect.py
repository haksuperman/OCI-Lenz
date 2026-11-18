"""Scoped FastConnect inventory; authentication and device settings never persist."""


def collect_fastconnect(call,add,compartment):
    for circuit in call('network','list_virtual_circuits',compartment_id=compartment) or []:
        mappings=[]
        for mapping in getattr(circuit,'cross_connect_mappings',None) or []:
            # CrossConnectMapping may contain a BGP MD5 key. Never copy the object.
            fields=('cross_connect_or_cross_connect_group_id','vlan','customer_bgp_peering_ip','oracle_bgp_peering_ip','customer_bgp_peering_ipv6','oracle_bgp_peering_ipv6')
            mappings.append({key:getattr(mapping,key) for key in fields if getattr(mapping,key,None) is not None})
        add(circuit,'virtual_circuit',gateway_id=getattr(circuit,'gateway_id',None),
            circuit_type=getattr(circuit,'type',None),bandwidth_shape_name=getattr(circuit,'bandwidth_shape_name',None),
            lifecycle_state=getattr(circuit,'lifecycle_state',None),bgp_session_state=getattr(circuit,'bgp_session_state',None),
            bgp_ipv6_session_state=getattr(circuit,'bgp_ipv6_session_state',None),is_transport_mode=getattr(circuit,'is_transport_mode',None),
            cross_connect_mappings=mappings)
    for group in call('network','list_cross_connect_groups',compartment_id=compartment) or []:
        add(group,'cross_connect_group',lifecycle_state=getattr(group,'lifecycle_state',None),minimum_links=getattr(group,'minimum_links',None))
    for connection in call('network','list_cross_connects',compartment_id=compartment) or []:
        add(connection,'cross_connect',cross_connect_group_id=getattr(connection,'cross_connect_group_id',None),
            lifecycle_state=getattr(connection,'lifecycle_state',None),port_speed_shape_name=getattr(connection,'port_speed_shape_name',None))

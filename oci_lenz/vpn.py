"""Scoped VPN metadata only. Never request shared secrets or device configuration."""


def collect_vpn(call,add,compartment):
    for cpe in call('network','list_cpes',compartment_id=compartment) or []:
        add(cpe,'cpe',ip_addresses=[cpe.ip_address] if cpe.ip_address else [])
    for connection in call('network','list_ip_sec_connections',compartment_id=compartment) or []:
        add(connection,'ipsec',cpe_id=connection.cpe_id,drg_id=connection.drg_id,
            static_routes=list(getattr(connection,'static_routes',None) or []),
            lifecycle_state=getattr(connection,'lifecycle_state',None))
        for tunnel in call('network','list_ip_sec_connection_tunnels',connection.id) or []:
            add(tunnel,'ipsec_tunnel',ipsec_id=connection.id,
                ip_addresses=[tunnel.vpn_ip] if getattr(tunnel,'vpn_ip',None) else [],
                cpe_ip=getattr(tunnel,'cpe_ip',None),status=getattr(tunnel,'status',None),
                routing=getattr(tunnel,'routing',None),lifecycle_state=getattr(tunnel,'lifecycle_state',None))

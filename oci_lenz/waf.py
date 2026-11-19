"""Regional WAF enforcement points; no rule payloads or inferred origins."""


def collect_waf(call,add,snapshot,compartment):
    for obj in call('waf','list_web_app_firewalls',compartment_id=compartment) or []:
        backend=getattr(obj,'backend_type',None)
        add(obj,'waf',backend_type=backend,
            load_balancer_id=getattr(obj,'load_balancer_id',None) if backend=='LOAD_BALANCER' else None,
            web_app_firewall_policy_id=getattr(obj,'web_app_firewall_policy_id',None),
            lifecycle_state=getattr(obj,'lifecycle_state',None))
        if backend!='LOAD_BALANCER':
            snapshot['coverage'].append({'region':snapshot['scope']['region'],
                'compartment':compartment,'service':'waf','resource_type':'web_app_firewall_backend',
                'status':'unsupported'})

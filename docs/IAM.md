# Read-only API permissions

The app never creates policies. The operator provides an existing API-signing profile and an authorized compartment/region. `read` includes inspect; "read-only account" must actually have each required permission. No instance metadata or userdata are persisted.

| API | Resource type / verb |
| --- | --- |
| ListRegionSubscriptions | tenancy subscription visibility; see Identity policy reference |
| ListCompartments | inspect compartments at tenancy scope, subject to ACCESSIBLE filtering |
| ListVcns | inspect vcns |
| ListSubnets | inspect subnets |
| ListRouteTables | inspect route-tables |
| ListNetworkSecurityGroups | inspect network-security-groups |
| ListNatGateways | inspect nat-gateways |
| ListInternetGateways | inspect internet-gateways |
| ListServiceGateways | inspect service-gateways |
| ListInstances | read instances (INSTANCE_READ), not only inspect |
| ListVnicAttachments | read vnic-attachments plus inspect instances |
| GetVnic | read vnics |
| ListPrivateIps | inspect private-ips |
| ListLoadBalancers | inspect load-balancers |
| ListBackendSets, ListBackends | read load-balancers for backend details |
| SearchResources | visibility follows permissions of the searched resource types; results are not a completeness guarantee |

404 can mean not found or hidden by authorization; coverage labels it `not_found_or_not_authorized`, not success with zero records. The source region/compartment/service/API is recorded for every call; raw error messages are discarded.

Authoritative references (verify against tenancy policies before use):
- https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/corepolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/lbpolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/iampolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Search/Concepts/queryoverview.htm

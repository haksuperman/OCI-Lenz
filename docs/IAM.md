# Read-only API permissions

The app never creates policies. The operator provides an existing API-signing profile and an authorized compartment/region. `read` includes inspect; "read-only account" must actually have each required permission. No instance metadata or userdata are persisted.

| API | Resource type / verb |
| --- | --- |
| ListRegionSubscriptions | tenancy subscription visibility; see Identity policy reference |
| GetTenancy | TENANCY_INSPECT for the tenancy name only |
| ListCompartments | inspect compartments at tenancy scope, subject to ACCESSIBLE filtering |
| GetCompartment | inspect compartments (COMPARTMENT_INSPECT); selected name fallback when absent from ListCompartments |
| ListVcns | inspect vcns |
| ListSubnets | inspect subnets |
| ListRouteTables | inspect route-tables |
| ListNetworkSecurityGroups | inspect network-security-groups |
| ListNatGateways | inspect nat-gateways |
| ListInternetGateways | inspect internet-gateways |
| ListServiceGateways | inspect service-gateways |
| ListDrgs | inspect drg-object (DRG_READ); inspect drgs includes it |
| ListDrgAttachments (attachment_type=ALL) | inspect drg-attachments (DRG_ATTACHMENT_READ); inspect drgs includes it |
| ListLocalPeeringGateways | inspect local-peering-gateways (LOCAL_PEERING_GATEWAY_READ) |
| ListRemotePeeringConnections | inspect remote-peering-connections (REMOTE_PEERING_CONNECTION_READ) |
| ListCpes | inspect cpes (CPE_READ) |
| ListIPSecConnections | inspect ipsec (IPSEC_CONNECTION_READ) |
| ListIPSecConnectionTunnels | inspect ipsec (IPSEC_CONNECTION_READ), selected connection only |
| ListVirtualCircuits | inspect virtual-circuits (VIRTUAL_CIRCUIT_READ) |
| ListCrossConnectGroups | inspect cross-connect-groups (CROSS_CONNECT_GROUP_READ) |
| ListCrossConnects | inspect cross-connects (CROSS_CONNECT_READ) |
| ListDbSystems | inspect db-systems (DB_SYSTEM_INSPECT) |
| ListDbNodes | inspect db-nodes (DB_NODE_INSPECT), with selected DB System filter |
| ListInstances | read instances (INSTANCE_READ), not only inspect |
| ListVnicAttachments | read vnic-attachments plus inspect instances |
| GetVnic | read vnics |
| ListPrivateIps | inspect private-ips |
| ListLoadBalancers | inspect load-balancers |
| GetLoadBalancer | read load-balancers; allowlisted listener protocol/port/default backend set only |
| ListBackendSets, ListBackends | read load-balancers for backend details |
| SearchResources | visibility follows permissions of the searched resource types; results are not a completeness guarantee |

404 can mean not found or hidden by authorization; coverage labels it `not_found_or_not_authorized`, not success with zero records. The source region/compartment/service/API is recorded for every call; raw error messages are discarded.

Authoritative references (verify against tenancy policies before use):
- https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/corepolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/lbpolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/iampolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/iampolicyreference.htm
- https://docs.oracle.com/en-us/iaas/Content/Search/Concepts/queryoverview.htm
- https://docs.oracle.com/en/cloud/paas/base-database/guide/policy-details.html
- https://docs.oracle.com/en/engineered-systems/exadata-database-exascale/exdxs/exadb-xs-policy-details.html (shared ListDbNodes permission table)

Base DB network addresses reuse GetVnic/ListPrivateIps permissions above. The
collector never connects to a database or reads passwords, wallets, SSH keys or
connection strings. IAM policies are not created or modified.

IPSec collection deliberately does not call GetIPSecConnectionTunnelSharedSecret,
GetIPSecConnectionDeviceConfig or any CPE/device template/configuration API.
`inspect cpes` covers ListCpes; `inspect ipsec` covers the connection and
tunnel List operations;
`read ipsec` additionally grants device-config/secret access and is
not required by this feature. No tunnel BGP authentication fields are retained.
See the [Oracle core verb/resource permission table](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/corepolicyreference_topic-Details_for_Verb__ResourceType_Combinations.htm).

FastConnect metadata uses only the three List APIs above. No LOA, device config,
MACsec secret or BGP-key API is called. ListVirtualCircuits can include a
CrossConnectMapping.bgp_md5_auth_key: the collector explicitly excludes it and
never serializes raw SDK objects. Provider keys/account IDs, customer-reference
fields, tags and MACsec properties are also omitted. State metadata does not
verify BGP route exchange or application reachability. Permissions follow the
[Oracle core policy table](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/corepolicyreference_topic-Details_for_Verb__ResourceType_Combinations.htm).

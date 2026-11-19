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

## 확장 DB 서비스 권한

기존 지역·컴파트먼트 필터와 읽기 전용 프로필을 그대로 사용한다. 다음은 호출하는
추가 API와 필요한 권한이다. 정책은 운영자가 준비하며 앱은 생성·수정하지 않는다.

| API | 필요 권한 또는 범위 |
| --- | --- |
| MySQL ListDbSystems | MYSQL_INSTANCE_INSPECT |
| MySQL GetDbSystem | MYSQL_INSTANCE_READ; 실패하면 System 목록은 보존하지만 Subnet/NSG는 미확인 |
| ListAutonomousDatabases | AUTONOMOUS_DATABASE_INSPECT |
| ListAutonomousContainerDatabases | AUTONOMOUS_CONTAINER_DATABASE_INSPECT |
| ListAutonomousExadataInfrastructures | AUTONOMOUS_EXADATA_INFRASTRUCTURE_INSPECT |
| ListAutonomousVmClusters | AUTONOMOUS_VM_CLUSTER_INSPECT |
| ListCloudAutonomousVmClusters | CLOUD_AUTONOMOUS_VM_CLUSTER_INSPECT |
| ListExadataInfrastructures, ListVmClusterNetworks | EXADATA_INFRASTRUCTURE_INSPECT; Network는 부모 Infrastructure 권한 상속 |
| ListVmClusters | VM_CLUSTER_INSPECT |
| ListCloudExadataInfrastructures | CLOUD_EXADATA_INFRASTRUCTURE_INSPECT |
| ListCloudVmClusters | CLOUD_VM_CLUSTER_INSPECT |
| ListExascaleDbStorageVaults | EXASCALE_DB_STORAGE_VAULT_INSPECT |
| ListExadbVmClusters | EXADB_VM_CLUSTER_INSPECT |
| ListDbNodes | DB_NODE_INSPECT; 선택 System 또는 VM Cluster ID 필터 |
| GetPrivateIp | PRIVATE_IP_READ; 관측된 SCAN PrivateIp ID만 조회 |

추가 네트워크 주소는 기존 GetVnic/ListPrivateIps 권한을 사용한다. 서비스별 목록이
거부되어도 다른 서비스는 계속 수집하며, 0건·403·404·일반 실패는 구분한다.
`coverage.request_scope`는 DbSystem/VM Cluster/Infrastructure ID 필터만 보존한다.
SQL, wallet 다운로드, Autonomous 접속 문자열 조회, SSH/DB 암호, MySQL Channel,
장비 설정 다운로드 API를 호출하지 않는다.

공식 근거:
- [MySQL API별 권한](https://docs.oracle.com/en-us/iaas/mysql-database/doc/api-operations.html)
- [Autonomous Dedicated IAM](https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/adbaa/iam-policies-for-autonomous-ai-database-on-dedicated-exadata.html)
- [ExaCC 정책](https://docs.oracle.com/en-us/iaas/exadata/doc/ecc-policy-details.html)
- [ExaCI 정책](https://docs.oracle.com/en/engineered-systems/exadata-cloud-service/ecscm/ecs-policy-details.html)
- [Exascale 정책](https://docs.oracle.com/en-us/iaas/exadb-xs/doc/exadb-xs-policy-details.html)


## Network Load Balancer

| API | 필요 권한 | IAM verb/resource |
| --- | --- | --- |
| ListNetworkLoadBalancers | NETWORK_LOAD_BALANCER_INSPECT | inspect network-load-balancers |
| ListListeners, ListBackendSets, ListBackends | NETWORK_LOAD_BALANCER_READ | read network-load-balancers |

모든 요청은 선택한 컴파트먼트의 NLB 및 해당 NLB/Backend Set으로 한정한다.
추가 Private IP ID는 기존 ListPrivateIps 결과에서만 보존하며 범위 밖 대상을
추적 조회하지 않는다. GetNetworkLoadBalancer/헬스/인증/쓰기 API는 호출하지 않는다.
정책은 사용자가 준비하며 앱은 IAM 정책을 생성하거나 수정하지 않는다.
공식 근거: [Oracle NLB IAM 권한표](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/nlbpolicyreference.htm).


## Regional WAF

| API | 필요 권한 | IAM verb/resource |
| --- | --- | --- |
| ListWebAppFirewalls | WEB_APP_FIREWALL_INSPECT | inspect web-app-firewall |

목록의 LoadBalancer summary subtype에 있는 보호 대상 ID만 사용하므로
GetWebAppFirewall(`WEB_APP_FIREWALL_READ`)이나 정책 Get/List·규칙/로그 API는
필요하지 않다. 보호 대상 LB는 기존 선택 범위의 LB 목록에서 확인한다. IAM 정책은
앱이 생성/수정하지 않는다. Legacy WAAS 권한은 이번 기능에서 요청하지 않는다.
공식 근거: [Oracle WAF IAM 권한표](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/wafpolicyreference_topic-Details_for_WAF_Policies.htm).

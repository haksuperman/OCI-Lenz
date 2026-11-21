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
앱이 생성/수정하지 않는다. Regional WAF 자체에는 WAAS 권한이 필요하지 않으며 Edge WAF 권한은 아래에서 설명한다.
공식 근거: [Oracle WAF IAM 권한표](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/wafpolicyreference_topic-Details_for_WAF_Policies.htm).


## Edge WAF / WAAS

| API | 필요 권한 | IAM verb/resource |
| --- | --- | --- |
| ListWaasPolicies | WAAS_POLICY_INSPECT | inspect waas-policy |
| GetWaasPolicy | WAAS_POLICY_READ | read waas-policy |

선택한 컴파트먼트 목록에서 반환된 정책 ID만 상세 조회한다. 위 권한은 Edge 정책
수집용으로 Regional WAF의 직접 LB 연결 권한과 별도다. 앱은 IAM을 변경하지 않으며,
DNS·외부 Origin·인증서·로그·규칙 전용 API를 호출하지 않는다. Get 응답에서도 필요한
Origin 필드만 보존한다. 정책 본문과 헤더는 원문으로 저장하지 않는다.
공식 근거: [Oracle Edge policy IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/wafpolicyreference_topic-Details_for_Edge_Policies.htm).

## OCI Cache · OCI Database with PostgreSQL · Search with OpenSearch

| SDK API | 필요 권한 | IAM verb/resource |
| --- | --- | --- |
| ListRedisClusters | REDIS_CLUSTER_INSPECT | inspect redis-clusters |
| GetRedisCluster | REDIS_CLUSTER_READ | read redis-clusters |
| PostgreSQL ListDbSystems | POSTGRES_DB_SYSTEM_INSPECT | inspect postgres-db-systems |
| PostgreSQL GetDbSystem, GetConnectionDetails | POSTGRES_DB_SYSTEM_READ | read postgres-db-systems |
| ListOpensearchClusters, GetOpensearchCluster | OPENSEARCH_CLUSTER_INSPECT (Oracle 공개 표의 List/GetElasticsearchCluster 명칭) | inspect opensearch-clusters |

Oracle OpenSearch 권한표는 List/Get 동작을 기존 Elasticsearch 명칭으로 표기한다.
OCI-Lenz는 현재 SDK의 List/GetOpensearchCluster만 호출한다. 실제 테넌시에서의
거부는 coverage에 남기며, 권한을 자동 상향하거나 manage 정책을 적용하지 않는다.
네트워크 목록/상세 조회는 기존 network read 권한으로 별도 수행한다. 생성·갱신용
VCN/VNIC 관리 권한, Redis 사용자/토큰 권한, DB 인증/SQL 권한, OpenSearch
인덱스/문서 접근 권한은 이 수집기에 필요하지 않다. GetConnectionDetails의
CA 인증서가 응답에 포함되더라도 주소 필드만 추출하고 인증서는 저장하지 않는다.

공식 근거: [OCI Cache IAM](https://docs.oracle.com/en-us/iaas/Content/ocicache/permissions.htm),
[PostgreSQL IAM](https://docs.oracle.com/en-us/iaas/Content/postgresql/policies.htm),
[OpenSearch IAM](https://docs.oracle.com/en-us/iaas/Content/search-opensearch/Concepts/ocisearchpermissions.htm).

## Oracle NoSQL Database Cloud Service

| API | 필요 권한 | IAM verb/resource |
| --- | --- | --- |
| ListTables | NOSQL_TABLE_INSPECT | inspect nosql-tables |

현재 수집기는 ListTables의 ID·이름·컴파트먼트·lifecycle만 사용한다.
GetTable(`NOSQL_TABLE_READ`), Query/GetRow, 인덱스·사용량·복제 API는 호출하지
않으므로 nosql-rows 접근 권한은 필요하지 않다. 스키마·DDL·태그·행 데이터도
저장하지 않는다. IAM 정책은 사용자가 준비하며 앱은 생성/변경하지 않는다.
공식 근거: [Oracle NoSQL 정책 참조](https://docs.oracle.com/en/cloud/paas/nosql-cloud/odsql/).

## Object Storage · Container Registry · DevOps metadata
| Service / API | Minimum permission | Resource verb |
| --- | --- | --- |
| Object Storage GetNamespace | No additional IAM permission for caller namespace | Authenticated caller; no compartment_id parameter |
| Object Storage ListBuckets | BUCKET_INSPECT | inspect buckets in selected compartment |
| Object Storage GetBucket (OCID only) | BUCKET_READ | read buckets in selected compartment |
| Registry ListContainerRepositories | REPOSITORY_INSPECT | inspect repos in selected compartment |
| DevOps ListProjects | DEVOPS_PROJECT_INSPECT | inspect devops-project |
| DevOps ListRepositories | DEVOPS_REPOSITORY_INSPECT | inspect devops-repository |
| DevOps ListBuildPipelines | DEVOPS_BUILD_PIPELINE_INSPECT | inspect devops-build-pipeline |
| DevOps ListDeployPipelines | DEVOPS_DEPLOY_PIPELINE_INSPECT | inspect devops-deploy-pipeline |
| DevOps ListDeployEnvironments | DEVOPS_DEPLOY_ENVIRONMENT_INSPECT | inspect devops-deploy-environment |

DevOps permissions are scoped to the selected compartment. Namespace lookup is
only a routing prerequisite for its buckets, not tenancy-wide bucket enumeration.
No object read/list, image pull, code fetch, build/deploy execution or IAM changes
are performed. GetBucket metadata is immediately reduced to the bucket OCID.
Sources: [Object Storage IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/objectstoragepolicyreference.htm),
[Registry IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/policyreference/registrypolicyreference.htm),
[DevOps IAM](https://docs.oracle.com/en-us/iaas/Content/devops/using/devops_iampolicies.htm).

## OCI GoldenGate (OCIGG)
| API | Minimum permission | Resource verb |
| --- | --- | --- |
| ListDeployments | GOLDENGATE_DEPLOYMENT_INSPECT | inspect goldengate-deployments in selected compartment |
| GetDeployment | GOLDENGATE_DEPLOYMENT_READ | read goldengate-deployments in selected compartment |

GetDeployment provides NSG metadata absent from DeploymentSummary. Its response is
allowlisted immediately; ogg_data, usernames, URLs and settings are not stored. No
connection/assignment/process/data API or deployment start/stop/update is called.
No IAM policies are applied by OCI-Lenz.
Source: [Oracle GoldenGate IAM](https://docs.oracle.com/en/cloud/paas/goldengate-service/ocigg/oracle-cloud-infrastructure-goldengate-policies.html),
[DeploymentSummary fields](https://docs.oracle.com/en-us/iaas/tools/python/latest/api/golden_gate/models/oci.golden_gate.models.DeploymentSummary.html).

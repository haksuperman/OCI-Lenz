# Oracle official OCI icons

Source: https://docs.oracle.com/en-us/iaas/Content/General/Reference/graphicsfordiagrams.htm
Archive: https://docs.oracle.com/iaas/Content/Resources/Assets/OCI-Style-Guide-for-Drawio.zip
File: OCI Style Guide for Drawio/OCI Library.xml (unmodified).
Oracle assets remain subject to Oracle's applicable terms; no project license is asserted for them.

Mapping (0-based library entries): VM=3, VCN/Subnet=17, LB=18, Route Table=29, Service Gateway=31, Internet Gateway=32, NAT Gateway=33, VNIC private endpoint=78, NSG=114. Official component labels are suppressed in diagrams; geometry/stencils stay editable. Subnets are logical boundaries; Backend Sets use editable name tags rather than a duplicated LB icon.

SHA-256: `e098244928cdd5257c1bc4696cf9f46fd289b4195208d699e5392bf79de69555`

Additional mappings: DRG=30, RPC=34 (Networking - Remote Peering Gateway).
The bundled toolkit has no dedicated LPG entry. LPG uses an editable logical name tag. Attachment cards are omitted from diagrams;
their API references provide direct DRG links. No unrelated icon is substituted.

Base Database mappings: DB System=36 (Database - Database System), DB Node=35
(Database). Overview uses one System icon with its Display Name and Node IPs;
individual Node icons are available in optional network details only.

IPSec: CPE=21 (Networking - Customer Premises Equipment CPE). Connections are native
API-owned containers; individual tunnels use editable child tags. Entry 211 is a vertical VPN
connector, not a resource stencil, and is deliberately not substituted.

FastConnect: Virtual Circuit and CrossConnect port symbols use the EXACT embedded
SVG from entry 210 (Physical - Special Connectors - FastConnect - Horizontal).
The SVG image cell is copied unchanged and scaled proportionally. Its native
connector arrow and stock caption are excluded: they are drawing decorations,
not OCI API relationships. The actual API connection lines and resource labels
remain separate editable Draw.io cells. The original library file is unchanged.
CrossConnectGroup is an API-owned physical-port container, not a substitute icon.

Database service expansion: MySQL uses entry 47, Autonomous DB 37, dedicated
Autonomous containers/cloud VM clusters 38, Exadata/cloud infrastructures and
VM clusters 43, and ExaCC infrastructures/VM clusters 44. Legacy Exadata DbSystems
also use 43. The pinned library has no dedicated Exascale or Storage Vault art:
Exadb VM Cluster reuses Exadata 43; Storage Vault and on-prem VM Cluster Network
are logical editable name tags, with no borrowed OCI Block Storage/VCN identity.


Network Load Balancer uses entry 18 (Networking - Load Balancer), the official
generic LB glyph. The pinned archive has no dedicated NLB entry. Native resource
kind and relationships distinguish NLB from classic LB; no invented artwork or
unrelated Flexible Load Balancer symbol is substituted.


Regional WAF uses entry 102 (Identity and Security - WAF), the official native
editable WAF stencil. WAF is outside subnet containers and points to the observed
protected load balancer; the artwork does not imply an additional proxy hop.


Edge WAF (WAAS) also uses official WAF entry 102. edge_waf is a separate logical
service type from regional waf; there is no claim of a distinct Edge stencil.
Unresolved configured origins use editable logical tags, not invented OCI icons.

Managed data services: OpenSearch uses original library entry 49. PostgreSQL
uses `postgresql.xml` entry 0, extracted from the SAME official Draw.io ZIP's
`OCI Architecture Diagram Toolkit v24.2.drawio`, Icons page, symbol group
`mREtu-c0wOV9HSzNNSta-1879` (10 native vector cells). The outer caption group is
excluded; the vector stencils/geometry are retained with the root origin reset.
Toolkit member SHA-256: `b544991da988625e147dbeb7623bacc1be96699e2415d7f4d548f0d2a532d59e`.
PostgreSQL library SHA-256: `521a72a44ebbfd5c54f6268daf3a744d4edb5bb6e606a69c0d2d503596f540c8`.
Oracle asset terms above also apply to this extracted geometry. No dedicated
Cache/Redis-named entry was found in the downloaded bundle. Cache now reuses
original library entry 46 (Database - NoSQL), matching the symbol used for
OCI Cache: Managed Redis on page 29 of Oracle's official presentation:
https://www.oracle.com/kr/a/ocom/docs/oracle-architecture-for-semantic-search-and-reliable-llm.pdf#page=29
This is reuse of an existing official symbol, not a new dedicated Cache stencil.
The distinct `nosql_table` kind also uses entry 46 for actual NoSQL table metadata.
No image or shape is redrawn; the original library hash remains unchanged.

## Regional storage and developer services
Unmodified native entries from the pinned `library.xml`:
- 11 — Storage - Object Storage → object_storage_bucket
- 75 — Developer Services - Container Registry → container_repository
- 85 — Developer Services - DevOps → project, code repository, build/deploy
  pipeline and deploy environment cards (service-symbol reuse, no dedicated child artwork).

OCI GoldenGate deployments use original library entry 51 — Database - GoldenGate.
This is the existing editable OCI GoldenGate service symbol, not entry 50's
on-premises product or a newly drawn raster image. The deployment card is placed
by the observed private endpoint subnet; the symbol does not describe service
internals or a replication relationship.

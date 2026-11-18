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

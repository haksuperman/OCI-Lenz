# FastConnect inventory and official graphics

Read AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR/IAM docs, collector/network/diagram
models, draw.py, network_layout.py and actual bundled Oracle library entries.
Input: explicit region/compartments and runtime read-only profile or synthetic
snapshot. Interface: shared paginated/retried API wrapper, canonical graph,
Attachment-free direct projection and native editable Draw.io/PNG.
Scope: ListVirtualCircuits/ListCrossConnectGroups/ListCrossConnects; exact
VirtualCircuit.gateway_id, mapping IDs and CrossConnect.group_id relationships.
Keep unknown endpoints, public/provider-managed distinctions and no invented CPE.
Use the unchanged official FastConnect SVG symbol from library entry 210 for
VC/physical-port objects, not the decorative connector line as an API edge.
Physical groups contain only their API-owned CrossConnect children. FastConnect
branches sit below their DRG, leaving existing VCN/VPN/RPC directions intact.
AC: failing real-SDK allowlist/denied-vs-empty/public/unknown/icon tests first;
exclude MD5/MACsec/provider credentials; full suite and unchanged prior replay;
synthetic Draw.io/PNG plus authorized live API counts or explicit zero/denied.
Prohibitions: IAM/OCI writes, raw responses/secrets, LOA/device config retrieval,
IP/name-based ownership inference, invented transit/reachability or physical
provider inventory, customer files in Git, agents, commits/pushes/executor edits.

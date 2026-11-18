# IPSec VPN metadata and relationships

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md,
USAGE.md and collect.py, network.py, model.py, architecture.py, typography.py.
Inputs: explicitly authorized region/compartments and local runtime SDK profile,
or independent synthetic snapshot. Interfaces: common snapshot, coverage and
API-evidenced graph; alias-only AI Draw.io generation and native PNG export.
Scope: ListCpes, ListIPSecConnections and each connection's paginated
ListIPSecConnectionTunnels. Preserve CPE/DRG references, tunnel request-scoped
ownership and actual tunnel attachment IDs. Cards show names and observed IPs;
status/routing/static routes remain appendix metadata, not reachability claims.
AC: failing tests before implementation, per-connection scope and SDK allowlist
tests, denied/zero/unknown endpoints, native editable CPE and logical VPN/tunnel
cards, full unit suite, synthetic Draw.io/PNG export and visual inspection.
Prohibitions: shared-secret/device-config APIs, raw responses, credentials, IAM
changes, remote-scope traversal, inferred traffic/service membership, customer
files in Git, agents, automatic commits/pushes or manual executor completion.
FastConnect, BGP route evaluation and tunnel configuration changes are excluded.

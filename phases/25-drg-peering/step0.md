# DRG and peering inventory

Read AGENTS.md, docs/HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, USAGE.md,
IAM.md, collect.py, model.py, draw.py and architecture.py. Verify the official
SDK model/API and IAM references; inspect existing official library titles.
Scope: scoped paginated ListDrgs, ListDrgAttachments(ALL), ListLocalPeeringGateways
and ListRemotePeeringConnections using existing read-only retry/coverage handling.
Allowlist attachment/peer identifiers and status only. Prefer network_details;
do not infer connectivity or query remote scopes. Resolve selected compartments
together; unresolved endpoints stay explicit. Keep old snapshots compatible.
Interfaces: common snapshot graph, alias-only scene and native editable output;
official DRG/RPC stencils, logical attachment/LPG labels if no dedicated stencil.
AC: SDK-model tests first; denied versus empty results differ; graph evidence and
out-of-scope peer tests pass; old plans replay identically; generate and inspect
synthetic Draw.io/PNG; document permissions and scope limits; full tests/harness.
Prohibitions: no IAM changes, write APIs, remote/tenancy auto-discovery, business
group inference, raw SDK responses/secrets/customer artifacts in Git, agents,
commits/pushes or executor status changes. DB/OKE, VPN/FastConnect endpoints and
DRG route-table/distribution policy evaluation remain follow-up work.

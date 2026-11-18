# Oracle Base Database infrastructure

Read AGENTS.md, HARNESS.md, PRD.md, ARCHITECTURE.md, ADR.md, IAM.md, USAGE.md,
collect.py, model.py, display.py, draw.py and architecture.py. Verify current
official Base DB/SDK/IAM references and the native toolkit DB System entry.
Scope: selected compartments' ListDbSystems and per-system ListDbNodes, limited
to VM/BM Base DB shapes. Preserve client/backup subnet, NSG and node VNIC evidence
using shared read-only retry/pagination/coverage. Unknown shapes are unsupported.
Interface: common snapshot/graph. Overview shows ONE DB System official icon,
its Display Name and observed client Node IPs only. Hide node hostname cards;
retain node/VNIC evidence and optional network details/appendix. Backend display
may project a hidden node onto its observed system, retaining validated physical
target evidence in XML. Do not invent an application-to-DB relationship.
AC: SDK-summary tests first; denied versus empty distinguished; secrets/tags
excluded; two-node captions and backend projection/tamper tests; full tests,
unchanged current examples, synthetic native Draw.io/PNG and visual inspection.
Prohibitions: no SQL connections/passwords/SSH keys/wallets/connection strings,
IAM changes, Exadata/Exascale/other engines mislabeled Base DB, inferred business
groups, customer artifacts in Git, commits/pushes, agents or executor edits.
DB Homes, logical databases/PDBs and Data Guard remain explicit follow-up scope.

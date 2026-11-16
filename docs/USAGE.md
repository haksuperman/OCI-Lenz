# Install and run

Python 3.10+, Git, authenticated Codex CLI, and Draw.io Desktop are required for the full flow. OCI API credentials are only required by collect. Codex authentication is separate from OCI API signing; the app does not manage OAuth or customer accounts.

```sh
git clone https://github.com/haksuperman/OCI-Lenz.git
cd OCI-Lenz
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
oci-lenz sample --output artifacts/sample
oci-lenz draw --snapshot artifacts/sample/snapshot.json --output artifacts/diagram
```

Project skills are available on the next Codex turn. The CLI also loads their pinned instructions explicitly. Default architecture design includes a bundled, independently synthetic composition image. To replace it add `--references /local/sanitized-reference-images`; supplied PNG/JPEGs become AI input. No customer reference pictures are bundled.

The default architecture style invokes the official jgraph Draw.io skill plus
the OCI adapter through the selected model provider. AI designs absolute
rectangles for every container and resource, plus optional edge waypoints.
Helpers apply those coordinates without replacing them with a fixed grid,
import native Oracle icons, apply real local labels, validate the graph and
export the same XML. Invalid geometry is returned to the model for up to two
repairs (three requests maximum); failure never silently switches to a template.
`--no-ai` explicitly uses a deterministic seed for diagnostics only.

## AI authentication on each installation

The default `--ai-provider codex` uses that user's local Codex CLI login:

```sh
codex login
codex login status
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --output /local/private-diagram --ai-provider codex --model YOUR_CODEX_MODEL
```

Omit --model to use the local Codex model. Architecture uses high reasoning
effort; legacy service-map uses low effort ordering hints. Each user signs in
independently; the app does not copy OAuth tokens or register accounts. Codex CLI
is needed only for the Codex provider.

For a direct OpenAI Responses API connection, set OPENAI_API_KEY in the runtime
environment using a local secret manager. Do not put literal keys in commands,
project files, snapshots or logs. Choose a vision/structured-output capable
model available to that account:

```sh
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --output /local/private-diagram --ai-provider openai --model YOUR_API_MODEL
```

OCI_LENZ_AI_PROVIDER and OCI_LENZ_AI_MODEL provide optional non-secret defaults.
The API adapter uses https://api.openai.com/v1/responses with store=false; this
does not change provider retention policies. Reference images go to the selected
provider. Names, OCIDs, IPs and credential/config contents do not: only alias IDs,
relationship kinds, subnet public/private flags and label footprints are sent.
API failures never print response bodies. API live execution requires a user key
and model; the transport adapter is tested with mocks.

The editable information-index page retains all collected addresses and network
configuration. Architecture cards show up to three detail lines and refer to
the index for additional addresses, so many secondary IPs do not inflate one VM.
PNG output includes information-index.png. Replay requires matching inventory
IDs and label footprints; mismatched plans are rejected. Old hint-only layouts
must be replayed with --style service-map.

Default output is one whole-environment architecture canvas, with an editable
Resource information appendix. VCNs and subnets are boundaries inside the same
canvas; no separate VCN architecture pages are created unless --detail-pages is
specified. Version-3 plans use a dedicated AI overview scene, excluding technical
VNIC/NSG/route cards from layout so they do not leave empty lanes. Native hidden
cells and all evidence are retained. Optional VCN detail pages use an independent
AI scene with the complete network inventory. Old version-2 plans remain replayable.
Local orthogonal routing avoids resource cards without changing model
placements. This checks geometry, not actual traffic reachability or universal
visual optimality. Sparse/dense, multiple compartments, unresolved targets, long
names and many secondary IPs are regression cases; new layouts still need visual
review before delivery.

Operational cards prioritize an observed primary-VNIC private address and public
address, when recorded; legacy snapshots use an observed representative address
without claiming it is primary. All addresses remain in the information index.
Listener protocol/ports and backend ports are labeled separately. New collection
uses GetLoadBalancer for allowlisted listener details and GetVnic primary fields.
Existing snapshots must be recollected for fields not previously stored.
Backend fanout shares a clear trunk only within one Backend Set; native evidence
edges are never merged. Mixed-direction layouts retain individual clear routes.

## Service presentation and visual review

Use explicit service groups when a business service spans multiple VCNs. The app
does not infer business ownership from resource names. Without group metadata it
keeps API-compartment grouping and evidenced backend flow. Store customer group
files outside the repository. Example local JSON:

```json
{"groups":[
  {"label":"Service A","vcn_ids":["VCN_OCID_1","VCN_OCID_2"]},
  {"label":"Shared services","role":"shared","vcn_ids":["VCN_OCID_3"]}
]}
```

Pass --groups /local/service-groups.json to draw. Resource membership and API
evidence are preserved; duplicate/unknown VCN assignments are rejected. Supply
the same group file on replay. Native name labels are bold; address/port labels
are smaller and muted. Unicode-aware measurement computes card heights.

Fresh architecture generations with PNG output run model visual review by
default. A separately rendered preview masks names, addresses and group labels
while preserving geometry/text footprints. PNG textual metadata and embedded XML
are rejected. The model sees the preview plus the selected reference images and
may revise the complete overview geometry. Every revision undergoes evidence,
clipping and overlap validation. --review-rounds 1 (default) permits one revision
and a final inspection; 2 permits two revisions. Remaining issues are recorded
as needs_review in visual-review.json, not reported as a pass. Human acceptance
is still required for subjective quality.

--review-rounds 0 explicitly disables visual review. --no-ai, --no-png and saved
layout replay make no additional review calls. Review adds model latency/cost
and requires Draw.io Desktop for the masked preview. Original customer images
and unmasked customer output PNGs are not automatically uploaded.

```sh
oci-lenz draw --snapshot artifacts/sample/snapshot.json --output artifacts/repeat \
  --reuse-layout artifacts/diagram/skill-layout.json
oci-lenz collect --profile READONLY --region REGION \
  --compartment-id COMPARTMENT_OCID --output /local/private-output
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --references /local/reference-images --output /local/private-diagram
```

Set `--config-file /path/to/config` and optional `--vcn-id OCID` on collect. Repeat `--compartment-id` to explicitly include multiple compartments. Their snapshots are combined before relationship resolution; references outside that set stay unresolved. No automatic tenancy-wide crawl. An attached VNIC is fetched to establish instance relationships. Profile keys/passwords are read by the SDK only.

Default output is an operational customer diagram: actual names, observed private
and public VNIC addresses (including secondary VNICs), LB addresses, backend
endpoints, network CIDRs and route destinations are retained. Keep all real
snapshots, Draw.io files and PNGs outside Git. The collector stores only needed
fields; older snapshots lack public IP/LB/CIDR fields and must be recollected to
add them. Missing addresses are never inferred. Names/IPs are applied locally;
Codex still receives only alias IDs, types and relationship structure.

For a separate sharing PNG, explicitly use `draw --redact`: visible names, IPs,
group names and non-default route destinations are hidden. This is not a complete
anonymizer for Draw.io XML: cell IDs still contain internal identifiers. PNGs
never embed XML. GitHub examples must use synthetic data and undergo publication
review; do not publish customer-derived files merely because --redact was used.

Outputs: architecture.drawio, region.png, vcn-N.png, coverage.json, validation.json and (with AI) skill-layout.json. VCN PNG ordering follows VCN IDs. PNGs are exported from the same XML and the XML is retained. Region page currently shows the full scoped inventory; large inventories may need future pagination. Reference count and input image size should be kept modest for Codex.

## Draw.io on servers

Set `DRAWIO_BIN` to the Draw.io Desktop executable. macOS's standard installation is detected automatically. On Linux install the Draw.io Desktop package and Xvfb using the server's package manager. When no DISPLAY is set and `xvfb-run` is available, the exporter wraps Desktop with it. Do not disable the Electron sandbox. Linux server execution has not yet been exercised in this repository's validation.

## Diagnose

The draw command reports when AI layout starts and when PNG export starts.
Codex layout uses a temporary working directory and a JSON-only subtask with the
pinned skills explicitly provided; no project files or source names are needed
by the child. The default AI timeout is 600 seconds per request;
use `--skill-timeout 900` to allow 15 minutes. A timeout reports the stage without
printing the child command or output. There is no automatic AI bypass. For an
explicit local-only diagnostic run use `--no-ai`; this does not invoke Codex.
After a successful layout, `skill-layout.json` can be reused to retry PNG export
without another model call. PNG export still has a 120-second limit per page.

Run `python3 -m unittest discover -s tests -v`, `codex login status`, and `"$DRAWIO_BIN" --help` locally. Child output is suppressed to avoid persisting sensitive data; errors report only their class. SDK API failures are summarized in coverage by service/API/status, not raw exception text. A partial snapshot is still usable; coverage must be checked. Reuse a saved layout to avoid another model call. `--no-png` retains XML without requiring Desktop.

Current limitations: real OCI access and user reference-image style acceptance require their respective inputs; complex and large graph layouts need further visual evaluation. Backend Sets use the LB icon as a conceptual grouping. Public/private subnet containers use VCN visual grouping. The model preserves all subnet associations even though a multi-subnet LB is placed once, in its first subnet.

## Synthetic architecture overview

```sh
python3 -m oci_lenz sample --scenario overview --output artifacts/reference-layout
python3 -m oci_lenz draw --snapshot artifacts/reference-layout/snapshot.json --output artifacts/reference-layout
python3 -m oci_lenz draw --snapshot artifacts/reference-layout/snapshot.json \
  --reuse-layout artifacts/reference-layout/skill-layout.json --output /tmp/oci-lenz-replay
```

This independently synthetic scenario contains two compartments and three VCNs.
Region and VCN pages use neutral region/compartment frames and orange dashed
network boundaries, with container sizes calculated from their contents. API
compartment membership controls VCN grouping; application service groups are not
guessed. A VCN without compartment metadata is grouped in an unspecified alias
compartment. Related resources from other compartments remain in their evidenced
network location. Dense cross-container edges may still need manual refinement.
The saved card layout reproduces XML exactly; PNG bytes may depend on Desktop and
fonts. No customer images or identifying text are bundled or required by this example.
Reference images passed with `--references` go to Codex, so sanitize them first;
the customer originals supplied in chat have not been passed to a child model.

## Legacy adaptive service architecture layout

```sh
python3 -m oci_lenz sample --scenario service-map --output artifacts/main-reference
python3 -m oci_lenz draw --snapshot artifacts/main-reference/snapshot.json \
  --style service-map --output artifacts/main-reference
python3 -m oci_lenz draw --snapshot artifacts/main-reference/snapshot.json \
  --style service-map --reuse-layout artifacts/main-reference/skill-layout.json \
  --output /tmp/oci-lenz-service-replay
```

The main reference guides resource spacing, backend flow and visual hierarchy;
its canvas dimensions, customer topology and number of panels are not templates.
Subnet grids grow with the number of cards, related backends stay adjacent, VCNs
wrap into shelves and region size follows the resulting content. Small and large
inventories use the same renderer. Codex supplies stable ordering hints; the
helper fits them to a compact grid and preserves the evidence graph.

Optional snapshot presentation metadata declares user-controlled service groups:

```json
{"presentation":{"groups":[
  {"label":"Example service","vcn_ids":["synthetic-vcn"]},
  {"label":"Shared services","role":"shared","vcn_ids":["synthetic-shared-vcn"]}
]}}
```

Groups are presentation metadata, not OCI resources or discovered application
semantics. The collector does not infer service membership. Without groups,
VCNs are automatically grouped by their API compartment IDs; unmatched VCNs in a
partial mapping also fall back to compartment groups. Explicit `--redact` outputs
alias group names as well as resource names. Use `--style inventory` for the
previous compartment inventory renderer.

The overview keeps editable technical cells and every relationship in XML but
hides VNIC/NSG/route-table shapes and technical edges. VCN detail pages show them.
The LB-to-Backend-Set display arrow expresses ownership while the XML source and
target retain the API evidence direction (`BackendSet.lb_id`). Backend arrows
represent configured targets, not proven traffic. Dense detail edges can still
share segments and may require editing. No DB or WAF resources are added from a
picture. Unknown targets remain visible. The fixture is independently synthetic;
no customer image is sent to the child Codex process.

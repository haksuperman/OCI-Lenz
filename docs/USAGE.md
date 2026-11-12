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

Project skills are available on the next Codex turn. The CLI also loads their pinned instructions explicitly. For visual examples add `--references /local/reference-images`; supplied PNG/JPEGs become AI input. No user reference pictures are bundled.

The draw command invokes the official jgraph Draw.io skill plus the OCI adapter. Codex provides the card layout; deterministic skill helpers import the editable Oracle stencils, construct nested XML, validate the graph and export PNGs. It is not an online draw.io service and does not require browser automation. `--no-ai` explicitly runs only the deterministic helper, useful for tests.

```sh
oci-lenz draw --snapshot artifacts/sample/snapshot.json --output artifacts/repeat \
  --reuse-layout artifacts/diagram/skill-layout.json
oci-lenz collect --profile READONLY --region REGION \
  --compartment-id COMPARTMENT_OCID --output /local/private-output
oci-lenz draw --snapshot /local/private-output/snapshot.json \
  --references /local/reference-images --output /local/private-diagram
```

Set `--config-file /path/to/config` and optional `--vcn-id OCID` on collect. Repeat `--compartment-id` to explicitly include multiple compartments. Their snapshots are combined before relationship resolution; references outside that set stay unresolved. No automatic tenancy-wide crawl. An attached VNIC is fetched to establish instance relationships. Profile keys/passwords are read by the SDK only. Keep real snapshots/output outside Git. Diagram identifiers may contain OCIDs even when visible labels are aliases; treat Draw.io files as private. PNGs contain aliases and no embedded XML. Route destinations are configuration data; inspect output before sharing.

Outputs: architecture.drawio, region.png, vcn-N.png, coverage.json, validation.json and (with AI) skill-layout.json. VCN PNG ordering follows VCN IDs. PNGs are exported from the same XML and the XML is retained. Region page currently shows the full scoped inventory; large inventories may need future pagination. Reference count and input image size should be kept modest for Codex.

## Draw.io on servers

Set `DRAWIO_BIN` to the Draw.io Desktop executable. macOS's standard installation is detected automatically. On Linux install the Draw.io Desktop package and Xvfb using the server's package manager. When no DISPLAY is set and `xvfb-run` is available, the exporter wraps Desktop with it. Do not disable the Electron sandbox. Linux server execution has not yet been exercised in this repository's validation.

## Diagnose

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

## Adaptive service architecture layout (default)

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
partial mapping also fall back to compartment groups. Default shared outputs
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

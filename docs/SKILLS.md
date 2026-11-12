# Draw.io skill provenance

The project vendors jgraph/drawio-mcp's official Codex Draw.io skill at commit cfc1b916b9deaa7c78d23d719d4124bd76d2d0bf, path plugins/codex/drawio/skills/drawio, under .agents/skills/drawio. Its Apache-2.0 LICENSE is included. Installed with skill-installer using git transport after the Python download encountered a certificate-store error; certificate verification was not disabled.

Evaluated the official skill against third-party Draw.io skills. Selected the official skill for native XML and Desktop export support with fewer runtime dependencies. Project OCI instructions preserve the XML alongside PNG and do not auto-open output. Helpers are implemented in oci_lenz/draw.py; Codex layout invocation is in oci_lenz/cli.py. Reference images are visual input, topology always comes from API evidence.

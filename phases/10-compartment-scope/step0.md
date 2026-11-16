# Compartment-only collection scope

Read AGENTS.md, HARNESS, PRD, ARCHITECTURE, ADR, USAGE, CLI and collector tests.
Inputs: explicit region, one or more compartment IDs and local SDK profile;
synthetic mocked inventories only for validation.
Interfaces: collect(profile, region, compartment, config_file=None); CLI collect
retains --compartment-id repetition and removes --vcn-id.
Scope: remove both CLI and SDK VCN filters; retain all returned supported
resources and existing cross-compartment relationship resolution. Update docs.
AC: tests first demonstrate removed-option rejection before SDK access, no VCN
filter interface and complete multi-compartment/multi-VCN inventory preservation;
full unittest suite passes; phase checks pass; saved synthetic layout still
renders validated Draw.io and PNG.
Prohibitions: no live OCI calls, credential inspection, service inference, IAM
changes, automatic Git publication or executor state changes. Do not remove
vcn_id evidence fields or optional VCN output pages.

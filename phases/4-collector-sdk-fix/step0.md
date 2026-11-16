# Collector SDK contracts

Read AGENTS.md, docs/HARNESS.md, PRD, ARCHITECTURE, ADR, USAGE,
oci_lenz/collect.py, model.py and tests/test_collect.py.
Inputs: installed OCI SDK models and synthetic mocked API responses.
Interface: collect(profile, region, compartment, config_file=None, vcn_id=None).
Scope: reproduce AttributeError with an actual SDK Vnic model, use its private_ip
field, retain secondary Private IPs, and exclude missing IP values from matching.
Also reproduce the keyword-only ListNetworkSecurityGroups SDK signature, pass
compartment_id by keyword, and verify successful NSG resource and coverage output.
AC: actual-model regression tests fail before the fix and pass after it; all
unittest checks and harness structure checks pass. IP fallback still works when
ListPrivateIps is denied and coverage records the denial distinctly.
Prohibitions: no credentials/config reads, live OCI calls, raw response logging,
IAM changes, Git publication, agents, or manual executor status changes.

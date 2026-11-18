# Independent PR dependency validation
Read AGENTS.md, HARNESS/PRD/ARCHITECTURE/ADR, quality.py, packaging workflow and
module-origin tests. Input: PR #16 checkout and CI ModuleNotFoundError for an
unpublished database expansion module. Scope: restore supported Base DB fanout
kinds without importing a separate collector feature. Test that every loaded
application module resolves inside this checkout even if a different editable
installation exists. Use a clean non-editable install for full suite and outside-
checkout package smoke validation. Confirm both CI Python matrix versions.
AC: module-origin regression fails before fix; full suite on clean environment;
installed CLI sample and XML draw outside checkout; current PNG replay remains
valid; CI is green for the new commit. Prohibitions: adding out-of-scope database
features, relaxing/skipping failing tests, masking dependency failures, customer
inputs/OCI calls or secrets, manual phase completion or changing executor AC.

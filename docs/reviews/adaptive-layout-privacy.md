# Adaptive layout publication review

Reviewed on 2026-11-12 before creating `feat/adaptive-service-layout`.
Proposed PR: `feat: adapt OCI architecture layout to inventory size`.
Base: `feat/oci-drawio` (existing application PR is still open).

Scope: tracked and untracked publishable files, staged content, all reachable
commit blobs, filenames, branch/PR text, synthetic fixtures, native diagram XML,
and generated PNGs including metadata. Ignored runtime credentials, virtualenvs,
and local intermediates are excluded from publication. Git identities are public
account/local development attribution; no customer identity is used. New commits
use the repository owner's GitHub noreply identity.

Methods: local pattern checks for private keys, access tokens, real OCIDs,
literal secret assignments, private customer paths/markers and literal email
addresses; snapshot synthetic-source checks; PNG text/EXIF chunk inspection;
manual source/diff review, provenance review and visual review of generated pages.
Compressed PNG pixel bytes are not treated as text matches; visible content is
reviewed separately. Oracle assets and upstream skill attribution are retained.
No customer reference image or identifying filename is included.

Result: no unresolved customer information, personal information or credential
findings in the publication set. Samples contain only independently synthetic
inventory. Private IP values in sample snapshots are synthetic fixture data;
shared PNGs show aliases and omit inventory IPs and embedded XML.

Validation: 39 tests passed with OCI SDK installed; harness structure checks and
`git diff --check` passed. The primary fixture has 75 resources, 125 relationships
and six pages. XML/PNG replay matched. Sparse (13) and dense (94) resource fixtures
also rendered. Full evidence is in `artifacts/main-reference/verification.json`.

Checks are repeated against staged files before push and against the committed
changes plus final PR text before PR creation. Pattern scans supplement manual
review and do not guarantee detection of every possible sensitive value. Actual
OCI collection and Linux headless export remain unvalidated and are not claimed.

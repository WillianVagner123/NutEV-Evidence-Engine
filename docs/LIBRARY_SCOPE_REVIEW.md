# Final visual review: library scope initialization

Scope: synthetic authenticated browser audit, not an observed production leak.

Review of the actual 2559780 browser screenshot exposed a coverage gap: a test
requested project scope while the page was still fetching its context, but the
page could rewrite that request to workspace scope before context initialization
completed. The previous screenshot consequently displayed workspace scope. The
same test asserted only nonempty full-text status, which accepted the loading
message rather than proving the permission request had resolved.

## Corrected behavior

Library scope/save/refresh controls start disabled in HTML and remain guarded
until trusted context is available. Early events cannot rewrite scope or submit
a placement. In-flight library loads carry a render generation; old responses
cannot replace the latest scope, and old cached entries are cleared during load.
The browser test now requires the selected project scope and its resolved status,
and waits for the explicit no-active-fulltext-access result, not a loading string.

A deterministic Node regression executes the production JS with initialization
held pending and library responses delivered out of order. Two new test cases
failed before the patch and passed afterwards. The full local suite reports
1,085 PASS. The stronger Chromium assertion requires a fresh run on the new SHA;
a former twelve-scenario PASS does not substitute for that execution.

No user account, real placement, scientific data, provider query, SSH key or
production configuration was modified. This correction prevents an implicit
scope choice; it does not redefine workspace sharing permissions or claim an
observed cross-tenant production exposure. Read the final exact-SHA PR comment
and artifacts for the completed new CI evidence.

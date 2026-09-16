# Security and quality audit

Type: first-party source review + adversarial tests + live verification, NOT independent professional audit. Delegated review failed with provider HTTP 401; no independent auditor endorsement is claimed.
Scope: contracts/grantweave.py, frontend/app.js/index.html, test and deployment harnesses.

## Findings repaired
1. Medium: uncertain-outcome validator compared full output in one branch, coupling free text to consensus. Infrastructure-failure branch also allowed unbounded explanation/extra fields. Fixed BEFORE deployment: require exact failure shape and bounded reason; grounded uncertain results use normal quote validation. Regression tests: test_uncertain_reason_may_differ, test_uncertain_cannot_drop_grounding, test_failsafe_rejects_unbounded_or_extra_fields.
2. Low: malformed HTML option made the open-map demonstration unavailable. Fixed after first browser run; public and local-server real flows subsequently completed.
3. Low, evidence harness only: browser logger captured previous transaction text before a new hash arrived. Fixed to require a changed hash. Original logs preserved; corrected mappings decoded from chain calldata; final pipeline asserts four unique hashes.
4. Low, harness expectation: ambiguous scope can be rejected for missing mandatory requirements instead of marked uncertain. Original expected-status assertion stopped smoke. No contract data altered to force a pass; observed mismatch and skipped scenarios are disclosed.

## Tests and controls inspected
- URL exact-host allowlist, commit pin, no query/fragment/traversal/userinfo/private-IP hosts.
- HTTP status, complete-body length, UTF-8 and SHA-256 checks before model use; no truncation-based acceptance.
- Per-source verbatim citations, all baseline coverage, enum/type validation; malformed or absent model response cannot reserve.
- Independent validator decisions and evidence digests; forged status/hash/quote/reason rejection.
- Deterministic allocation arithmetic, no double evaluation, authorization, capacity and input bounds.
- Frontend escapes returned content; tests exercise markup payload without script execution, error handling, finality-vs-execution distinction, layout and real SDK readback.
- Keys remain outside repository; no payable methods or outgoing value transfers. Browser burner is plaintext sessionStorage, explicitly testnet-only and lost on tab close.

## Residual risks / suitability
- HIGH for unrestricted public production use: permissionless creation can exhaust the 100-round registry; anyone can fill a round's eight slots. No fee/Sybil mitigation. Appropriate only for bounded demonstration/coordinated pilot, NOT hostile production admission.
- Semantic LLM fallibility and prompt injection remain risks even with grounded quotes and diverse consensus. Citations prove substrings, not sound inference, real authorship or factual truth.
- Consensus liveness: strict two-label agreement can fail on ambiguous inputs. Observed UNDETERMINED preserves PENDING state and blocks sequential progress until a later successful evaluation; no skip/timeout exists.
- Owner sealing control, first-come priority, no cancellation or appeal; session-wallet loss can leave owner-controlled rounds open indefinitely.
- The 12 KB gate runs after the HTTP response is received; remote retrieval memory/redirect/DNS enforcement depends on GenVM and GitHub infrastructure. No arbitrary-host SSRF is allowed by application validation.
- Within-round scope misses other rounds, external grants, identity fraud and truth of public documents. No legal or actual funding guarantee.
- Vendored SDK has no completed dependency-CVE audit. Test runner archive uses upstream release availability; reproduction may need pinning its digest/mirror for long-term supply-chain stability.

Conclusion: implemented and exercised as a bounded Studionet Project prototype with the above restrictions. Not suitable for custodial or unrestricted production use. No blanket security or injection-immunity claim.

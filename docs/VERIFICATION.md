# Verification report

Executed September 16–17, 2026. Testnet prototype; not a production certification.

## Actual results
- 97 real-contract gltest direct-mode tests passed. Web/LLM responses are mocked at their boundaries: evidence/direct-tests.log.
- GenVM: 3 lint checks and SDK validation passed: evidence/genvm-lint.log.
- Mocked browser integration: 10 named checks at desktop and mobile widths; evidence/browser-tests.json. These are UI integration tests, not live consensus.
- One-command real pipeline: `python scripts/pipeline.py` exited 0 with `PIPELINE_PASS: true`. Fresh local server, actual browser SDK, actual Studionet transactions, then independent Python SDK readback. Evidence: evidence/pipeline.json.
- Public GitHub Pages flow also reached RESERVED. Its original logger captured stale transaction labels; authoritative corrected labels are decoded from calldata in evidence/readback.json, not inferred from DOM text.
- Read-only verification: 7 existing rounds readable; allocation conservation holds in every round. 35 recorded transactions verified, 34 successful (including deployment), 1 UNDETERMINED. This is a snapshot, not a future total.
- Deployed source byte-for-byte equals contracts/grantweave.py: SHA-256 3627bd9189e29e9b58664f99e5f2c786eb7a55d04888aad1de5b26e128bee04d.

## Deployment
Contract: https://explorer-studio.genlayer.com/contracts/0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466
Deploy: https://explorer-studio.genlayer.com/tx/0x9d46623f976f28f62af5e0343d5414b47c14ba54bbaf0b8c163a587a78393bed
The contract was deployed from the working source before the test/UI commit was pushed; the byte-identity check is the authoritative link, not a claimed deployment commit.

## Final pipeline transactions
- create_round: https://explorer-studio.genlayer.com/tx/0x40aa98ed0799033810822fd8b57d9590f45120b44fa3f4597b9f2b052931f71b
- submit_proposal: https://explorer-studio.genlayer.com/tx/0x0fc848362b1937d45be036dc84be504274d913e7eb5f56a7016b048dd6cab458
- seal_round: https://explorer-studio.genlayer.com/tx/0x4f84a04f595727ac45e706fa15066870fb2bf6ae07a57a1c251b51302ff1cfba
- evaluate_next: https://explorer-studio.genlayer.com/tx/0x5afc4f096b5ff72e3076ade034a8eaf57e6b7ffa3b6e3d29f46e8fedb02049da

## Observed judgments
- gw-distinct-1/2/3: RESERVED, 60/100 credits remaining in each.
- gw-overlap: RESERVED, REJECTED (duplicate), OVER_BUDGET, REJECTED (ineligible), REJECTED (insufficiently specified proposal). Remaining 20/60.
- browser-1789582876: empty round left by initial browser attempt before a malformed option tag was fixed. Preserved honestly.
- browser-1789583875 and browser-1789585481: each RESERVED, remaining 60/100.

## Failures and limits
The initial deployment polling request returned HTTP 403 with urllib; it was resumed by the SAME hash with requests. No duplicate deployment.
The intentionally vague proposal produced UNDETERMINED / MAJORITY_DISAGREE at 0x0a8ab7d8b3f687daac90bea2cafe1c1e92ceac94130557ff76012113a021fc77. A single retry 0x3ede3a4a7ce44615e148f57d961567e2fc23ab811d5d45b089399b3ba472b739 converged to REJECTED, not the harness's expected INCONCLUSIVE. The original smoke therefore did NOT pass as a whole. Both reject and uncertain avoid allocation, but the semantic difference is disclosed, not relabeled as a pass.
`gw-integrity` was never created: the original smoke stopped before that step. Missing-round errors were expected, not corrupt serialization. Hash-mismatch and completed-record guards are tested locally; no live coverage is claimed for those scenarios.
No GLSim, local Docker Studio, Bradbury or mainnet execution was performed. Studionet uses full consensus, not leader_only. Synthetic demo proposals are explicitly labeled. Quote grounding and consensus do not prove the LLM is correct or immune to prompt injection.

## Reproduce without new writes
`python scripts/verify_readback.py` re-reads existing rounds and transaction receipts; it never submits a transaction. It uses the saved testnet account only to satisfy SDK read requirements. Public receipts also have explorer links above.
The raw original logs are preserved, including failure tracebacks and stale browser labels. evidence/readback.json is the correction authority.

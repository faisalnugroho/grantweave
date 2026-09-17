# Public release verification

## Frozen deployment

Repository: https://github.com/faisalnugroho/grantweave
Production dashboard: https://faisalnugroho.github.io/grantweave/
Runtime configuration: https://faisalnugroho.github.io/grantweave/deployment.json
Contract: https://explorer-studio.genlayer.com/contracts/0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466
Deployment transaction: https://explorer-studio.genlayer.com/tx/0x9d46623f976f28f62af5e0343d5414b47c14ba54bbaf0b8c163a587a78393bed
Network: Studionet; chain ID 61999 (also verified by eth_chainId).

No contract, application or runtime configuration changes in this release. No contract or frontend redeployment. Publication uses `[skip ci]` to suppress push-triggered workflows, including Pages. This intentionally does not claim a new GitHub Actions run; local suite output is published instead.

Deployed Python source SHA-256: `3627bd9189e29e9b58664f99e5f2c786eb7a55d04888aad1de5b26e128bee04d`. Decoded deployment transaction source equals the repository contract bytes. Production `index.html`, `app.js`, `styles.css`, SDK bundle and `deployment.json` were each fetched and byte-compared with intended repository files. This is a single-page dashboard; wallet, creation, submission, sealing, evaluation and ledger are views/actions on the root page, not unverified separate application routes.

## Fresh production browser verification

The actual public Pages URL—not localhost—was exercised with Playwright, real browser SDK, a fresh session-only testnet burner and the testnet faucet. Round `browser-1789605149` completed:

- create_round: https://explorer-studio.genlayer.com/tx/0x0174d09a629b30a8375fd25c17aa09b97dcd6b4592beb5343b153112170ea3b2
- submit_proposal: https://explorer-studio.genlayer.com/tx/0x12241f7c750992a7eb3b8101c7deff09d0e2f835b8f4ca3aae6e0988d3ebb56f
- seal_round: https://explorer-studio.genlayer.com/tx/0xb6dae4fb2a529c6646e2ba28a712cf1b626494678300f91a564e5778cbf0489e
- evaluate_next: https://explorer-studio.genlayer.com/tx/0x8306fc9851913952dfd5bd1f0f63e44bed268f256ee465941b1759d5f69fa0f9

Every receipt passed execution/consensus checks. Calldata methods, round ID, submission metadata and contract recipient were independently verified. The accepted evaluation output equals independently fetched on-chain result; RESERVED, 40 credits reserved, 60/100 remaining. Browser recorded no page errors and rendered the matching ledger. This verifies the built-in burner workflow, not every external wallet provider.

Evidence:
- [Browser log](../evidence/release-browser.log), [browser JSON](../evidence/release-browser.json), [screenshot](../evidence/release-browser.png).
- [Independent readback, receipts and asset hashes](../evidence/release-preflight.json).
- [109-test fresh output](../evidence/release-tests.log). Earlier 12 targeted forensic regressions remain in [their original log](../evidence/forensic-targeted.log).

## Portal claims and public evidence

Use [VERIFICATION.md](VERIFICATION.md), [CONSENSUS_FORENSIC.md](CONSENSUS_FORENSIC.md), this release report and the linked public receipts. Historical failures and skipped scenarios remain disclosed. Raw files under the public repository's `evidence/` directory are downloadable supporting artifacts; localhost URLs or `/home/ubuntu/...` paths appearing inside historical logs are provenance only, **not suitable as Portal evidence URLs**. Use GitHub file URLs instead. No claim requires access to the Hermes filesystem or a private key. Some old reproduction scripts load a local signing account; public receipts and committed evidence do not require that account.

The project performs consensus-backed evaluation and conservative allocation. Accepted FAIL/DISTINCT yields REJECTED. Explicit UNCERTAIN or invalid/incomplete normalized responses yield INCONCLUSIVE; network disagreement is not an application verdict. Semantic ambiguity detection and labels are not perfectly deterministic. Neither hashes, quote grounding nor majority agreement prove semantic correctness or perfect security. Three fresh vague-proposal runs returned REJECTED; that is not a universal label guarantee. Testnet only; no production certification, payouts, global duplicate detection, application appeal, GLSim or Bradbury coverage is claimed.

The original 97-test report is historical; current suite is 109, including 12 forensic cases. Original failed smoke and skipped hash-mismatch live scenario were not deleted or relabeled.

Secret preflight checked tracked/intended files for private-key material, common credential patterns, sensitive filenames, and the known testnet account's actual private key without logging it. No findings. Receipt signatures, transaction hashes and validator environment-variable names are public metadata, not credentials. This is a bounded scan, not a claim that every imaginable secret encoding is detectable.

## Public commit verification procedure

After publishing, `scripts/release_public_verify.py <commit-sha> <output-path>` anonymously opens the public repository/commit, downloads every tracked file at that SHA and byte-compares it, verifies the production assets, opens Portal-facing URLs and validates explorer records and deployed-source identity. It has no deployment, transaction-write or Portal action. The final commit SHA and post-push verification result are reported by the release operator after those checks actually finish. This avoids a self-referential commit hash in the document.

Manual Portal submission remains the user's task. No Portal interaction was performed.

# GrantWeave

A GenLayer allocation desk for distinct public-goods deliverables. Different words can describe the same work: validators compare pinned proposal scope before the contract reserves allocation credits.

Dashboard: https://faisalnugroho.github.io/grantweave/
Contract (Studionet, 61999): [0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466](https://explorer-studio.genlayer.com/contracts/0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466)

## Use the project
1. Open the dashboard and create a testnet session (a burner stored only in this tab; never send real assets).
2. Create a round with an eligibility rubric and credit budget.
3. Add a public, commit-pinned raw GitHub `.md`/`.txt` proposal, SHA-256 and requested credits. The helper can fetch and hash a source. Labeled synthetic examples are available.
4. The owner seals submissions. Anyone can evaluate the next proposal.
5. Inspect the ledger, grounded quotations and transaction explorer links.

## Why GenLayer
The contract fetches complete, bounded documents, checks SHA-256 and asks validators to interpret eligibility and semantic scope overlap. The browser does not decide outcomes. Validators independently repeat the process, compare both decision labels and source hashes, and validate quotations. Deterministic code derives RESERVED, REJECTED, INCONCLUSIVE or OVER_BUDGET. Only RESERVED reduces the budget.

## Verification
- 97 direct-mode tests passed; web and LLM boundaries explicitly mocked.
- GenVM lint: 3 checks passed and contract validation passed.
- Desktop/mobile browser integration: explicitly mocked SDK/RPC.
- Public Pages browser flow completed with a real RESERVED result.
- A single complete local-server → browser → real Studionet writes → independent chain readback pipeline exited 0: `PIPELINE_PASS: true`.
- Readback verified deployed source equals repo bytes and budget conservation in all seven observed rounds; 35 transactions checked, 34 successful including deployment, one UNDETERMINED.

[Verification and failure history](docs/VERIFICATION.md) · [First-party audit and residual risks](docs/AUDIT.md) · [Project submission draft](docs/SUBMISSION_DRAFT.md)

Original live smoke did NOT pass every expectation: the vague proposal first caused consensus disagreement, then a single retry yielded REJECTED rather than expected INCONCLUSIVE. The unexecuted hash-mismatch live scenario is covered locally, not claimed as live proof. Original logs remain in evidence/; readback.json contains authoritative corrections to the old browser logger's stale labels.

## Important limits
- Credits are accounting units, NOT tokens, escrow, real grants or payouts.
- Only earlier RESERVED proposals in THIS round are compared. No global duplicate detector or identity proof.
- First-come priority; owner controls sealing; no cancellation/appeal/skip. Public submissions can fill eight slots; permissionless creation can exhaust the 100-round registry. Coordinated testnet prototype only, not unrestricted production.
- Exact bytes and grounded quotes do not prove truth, ownership or LLM correctness. Prompt injection and semantic errors remain possible.
- Model/source failure and uncertainty cannot reserve credits. Consensus disagreement leaves a proposal PENDING and may block sequential progress.
- Source body must be 20–12000 UTF-8 bytes. GitHub/network availability remains a dependency.
- No independent professional audit, mainnet, Bradbury or GLSim verification is claimed.

## Local verification
Python 3.12 is required. Run from the repo root:

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
mkdir -p ~/.cache/gltest-direct
curl -fLsS https://github.com/genlayerlabs/genvm/releases/download/v0.3.0-rc7/genvm-runners-all.tar.xz -o ~/.cache/gltest-direct/genvm-universal-v0.3.0-rc7.tar.xz
.venv/bin/python -m pytest tests/ -v
```

CI exercises this setup on a clean runner. gltest's contract-path-aware conftest resolves the pinned runner. Frontend tests additionally require Playwright (CI pins 1.58.0; local validation used 1.62.0): install Playwright and Chromium, serve frontend/ on 127.0.0.1:8766, then run scripts/browser_test.py. They use mocked network boundaries, clearly labeled.

`scripts/verify_readback.py` is read-only and uses the existing local testnet account under ~/.genlayer-keys/grantweave-key.json for SDK read requirements. Public transaction URLs are in docs/VERIFICATION.md.
`scripts/pipeline.py` makes real testnet writes: it starts/stops its own local server, runs the browser, and checks independent chain readback. Run deliberately; each invocation creates a new round.
`scripts/live_smoke.py` preserves the original scenario harness and its strict expected outcomes; do not blindly rerun it against already completed records.

## API and files
Writes: create_round(id,title,rubric,budget), submit_proposal(id,title,url,digest,amount), seal_round(id), evaluate_next(id).
JSON views: get_round(id), list_rounds().

contracts/ — Intelligent Contract; frontend/ — static dashboard and runtime deployment config; tests/direct/ — real contract tests; examples/ — labeled synthetic proposals; scripts/ — verification harnesses; evidence/ — raw receipts/logs/DOM evidence; docs/ — scope, audit, verification, submission.

Built during the week of September 14–20, 2026. Submission category: Project. No Portal submission has been filed.

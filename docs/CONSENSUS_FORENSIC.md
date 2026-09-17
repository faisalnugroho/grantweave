# Ambiguous-consensus forensic investigation

## Scope and classification

No contract modification or redeployment. Existing Studionet contract: `0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466`. Deployed source was fetched again and byte-compared against `contracts/grantweave.py`; SHA-256 `3627bd9189e29e9b58664f99e5f2c786eb7a55d04888aad1de5b26e128bee04d`.

Primary classification: **C**, nondeterministic external interpretation plus an over-specific smoke expectation. There is also an **A** component: REJECTED is the correct deterministic mapping of the actual accepted labels. This is not B: no evidence of an implementation mapping UNCERTAIN or MAJORITY_DISAGREE to REJECTED. D is not an adequate explanation: the proposal explicitly fails the rubric's specificity requirements, but its duplication scope really is underspecified. The prompt's UNCERTAIN instruction and the accepted DISTINCT interpretation are in tension; that limitation must remain visible.

## Why INCONCLUSIVE was expected

`scripts/live_smoke.py:137-145` places `examples/ambiguous.md` at index 4, amount 10, and unconditionally expects INCONCLUSIVE. Its exact text says: "We have not decided which artifacts, audience, rights or deliverables are involved. There is no concrete scope or delivery commitment."

The deployed prompt (`contracts/grantweave.py:157`) says "If sources lack enough scope detail, answer UNCERTAIN." Mapping at lines 202-205 gives either UNCERTAIN label precedence, even over FAIL or DUPLICATE. Thus the expectation is understandable, but the smoke incorrectly treats a natural-language instruction as a deterministic guarantee about LLM output. No scenario-name check or vague-text parser forces UNCERTAIN. `docs/PLAN.md` enumerates statuses and conservative allocation, not a guaranteed label for this document. `test_decision_matrix` covers all nine label pairs; these tests explicitly mock the labels and never establish live LLM determinism.

## Exact original execution path

1. **Input/configuration.** Round `gw-overlap`, rubric: "Only fund concrete public-goods deliverables that will be openly licensed and freely accessible without registration. Require a clear artifact, intended audience and delivery timeline." Budget 60; candidate index 4 requests 10; remaining 20. The candidate is pinned to commit `184a498947dc32ce3be089f77d3e3542ec24cec9`, `examples/ambiguous.md`, digest `9625d224d23f9068e7346aa410f1b86e6b8c6cc704f3f0dbecf0fb4dfce111f8`.
2. **Proposal/evaluation.** `evaluate_next('gw-overlap')` loads the sealed round's next index. It evaluates candidate source 0 plus only earlier RESERVED proposals. Here source 1 is `open-map.md`, digest `d300db59bc299f553e964be28261d8b5c95f8f063a77d5d7ee8012fe641f2407`. The rejected and over-budget proposals are not baselines. URL fetch, HTTP status, length, UTF-8 and exact body commitment checks run before the prompt.
3. **Leader output.** Both original and retry receipts decode to eligibility FAIL, duplication DISTINCT, both hashes and grounded quotes. The original leader rationale says missing artifact/audience/license/timeline fails the rubric and the work "appears different." The retry rationale says the scope is "too vague to duplicate the specific Open Map documentation manual." These are observed rationales, not independently established truths.
4. **Validator/consensus.** Each validator independently repeats fetch and model evaluation, compares BOTH labels and ordered hashes, then revalidates the proposed quotes. First transaction `0x0a8ab7d8b3f687daac90bea2cafe1c1e92ceac94130557ff76012113a021fc77`: 2 agree / 3 disagree; MAJORITY_DISAGREE. Retry `0x3ede3a4a7ce44615e148f57d961567e2fc23ab811d5d45b089399b3ba472b739`: 3 agree / 1 disagree / 1 idle; MAJORITY_AGREE. Idle receipt explicitly says cancelled after quorum. All three agreeing retry execution receipts are SUCCESS and have state hash `21c5c6df8f72ab29792080a083610daccc4c4955164e66bf910b12399b75cdf6`. Full-consensus mode and five initial validators are recorded; this was not leader-only execution.
5. **Normalization/mapping.** `normalize` preserves valid labels; it does not translate a consensus vote into an eligibility label. Invalid shapes, missing/invalid labels, missing baseline quotes, ungrounded quotes and infrastructure failures produce UNCERTAIN/UNCERTAIN. The accepted FAIL/DISTINCT has no UNCERTAIN, so line 202 is false and line 204 is true: REJECTED. The raw pre-normalization model response is not exposed by the saved RPC receipt; the normalized equivalence output is. Do not claim the unavailable raw response or each dissenting validator's independent labels were recovered.
6. **Persisted state.** The retry's complete decoded equivalence output equals `get_round('gw-overlap').proposals[4].result`, including its unique rationale, citations and hashes. Status REJECTED, next_index 5, remaining 20. No reservation was made. The failed first leader's different rationale is NOT the persisted rationale.
7. **Frontend/readback.** `frontend/app.js:19-21` requires successful execution AND MAJORITY_AGREE before reporting success, then reads `get_round`; line 17 renders `p.status` and `p.result` directly with escaping. No frontend verdict conversion occurs. The original vague evaluation was a Python smoke write, not a browser evaluation; its final state is nevertheless rendered from the same chain view.

### Receipt lifecycle correction

The original evidence recorded UNDETERMINED / MAJORITY_DISAGREE. Fresh RPC lookup now reports FINALIZED / MAJORITY_DISAGREE, while its historical status_changes end at REVEALING. Preserve both observations. FINALIZED alone is not evidence of an accepted state change. `succeeded(original)` remains false. The retry is FINALIZED / MAJORITY_AGREE / SUCCESS. This is not a relabeling of the first failure as a success.

## Trust boundary findings

- REJECTED cannot result from explicit UNCERTAIN or malformed/incomplete normalized model data along the ordinary deployed execution path. A semantically vague document CAN receive confident FAIL/DISTINCT model labels and then REJECTED; schema completeness is not epistemic certainty.
- INCONCLUSIVE means an accepted evaluation contained uncertainty or failed evidence/model validation. REJECTED means accepted, fully labeled ineligibility or duplication with neither label UNCERTAIN. Network disagreement is neither application status: it fails to commit the attempted transition, leaving it available for a later transaction.
- A minority does not decide the result. The initial 2/5 failed; retry 3/5 succeeded. An individual validator's SUCCESS or state hash, even when it votes disagree, is not sufficient evidence of acceptance. The contract delegates quorum enforcement to GenLayer; this investigation does not re-audit that protocol.
- The validator compares labels and hashes, not rationale equivalence. It checks quote membership/coverage, not whether a quote logically proves DISTINCT. The accepted rationale's "too vague to duplicate" versus the prompt's UNCERTAIN instruction is a real model-interpretation limitation. Consensus and hashes do not eliminate it.
- A new transaction can legitimately select different validators/models and rerun nondeterministic inference. Both observed leaders selected the same labels; what changed demonstrably was the validator set and vote outcome. Dissenting receipts expose `nondet_disagree: 0`, not the independent labels or which internal validator condition failed. A more specific claim would be a guess.
- Exact request binding: submission calldata binds title/URL/digest/amount to the persisted immutable proposal; creation calldata binds rubric/budget; evaluation calldata binds contract and round; sealed sequential state binds index; ordered output hashes bind candidate and baseline bytes; accepted output equality binds the persisted result. `evaluate_next` has no caller-supplied verdict and proposals have no update method. The result does not contain a standalone request-ID hash or transaction hash, so reconstruction uses these combined records rather than claiming such a field exists.
- Terminal decisions are immutable and there is no application appeal. Retry is appropriate only after an unsuccessful consensus transaction and an unchanged PENDING readback. A successfully persisted INCONCLUSIVE cannot be retried in place to hunt for a preferred result.

## Changes and regression policy

The original `scripts/live_smoke.py` and its failed expectation/logs remain unchanged as historical provenance. No failing test was deleted or xfailed. The new focused `scripts/forensic_live.py` supersedes only this scenario's fixed-label assertion: require no allocation, unchanged prior proposals and candidate metadata, exact next-index advancement, accepted quorum, output-to-state equality, pinned evidence and the correct mapping for whichever label actually occurs. RESERVED, OVER_BUDGET, a mislabeled INCONCLUSIVE, a minority receipt or a substituted request all fail the assertions. Exhausting three attempts is failure, not a skipped pass.

Three fresh rounds use identical evaluated rubric, candidate, reserved baseline, amounts and remaining budget. Prior non-RESERVED submissions are omitted because they are excluded by the deployed evaluation function; these rounds are not described as byte-identical full-state replays. The original five-proposal state is separately replayed in direct-mode regression tests.

`tests/direct/test_consensus_forensic.py`: 12 added cases cover captured FAIL/DISTINCT -> REJECTED and exact persisted result; FAIL/UNCERTAIN -> INCONCLUSIVE; missing eligibility or baseline grounding -> INCONCLUSIVE; validator label disagreement; original failed receipt; retry request/output/majority binding; and assertions rejecting allocations and semantic relabeling. Mocked boundary replays prove deterministic contract behavior, not new live LLM correctness.

Targeted: 12 passed. Complete direct-mode suite: 109 passed. Raw output: `evidence/forensic-targeted.log`, `evidence/forensic-suite.log`.


## Fresh execution results and final decision

- Targeted regressions: 12 passed. Complete suite rerun after harness edits: 109 passed.
- Three fresh ambiguous evaluations: REJECTED / REJECTED / REJECTED, all FAIL/DISTINCT, all first-attempt consensus acceptance. Each round remains at 20/60 credits. Exact output, request/calldata, candidate and baseline hashes, grounded citations, majority votes and agreeing state hashes passed the assertions.
  - `gw-forensic-1789601529-1`: `0xc3772f77cb9de0b31227bba4a60f3858737c563b163efc79ab850af02abfa179`
  - `gw-forensic-1789601529-2`: `0xc179972099519649ad81d535f78256432ff6cf39f80d1cec65063a71672f27d7`
  - `gw-forensic-1789601529-3`: `0xd7ab54b5a9144851a03fc3da2e6034cbf5b7f5c2daf55c5405ffdb1d81acadc0`
- Public browser flow: `browser-1789601543`, RESERVED, remaining 60/100, no page errors. Four distinct transactions were independently fetched and calldata/recipient verified:
  - create: `0xd0d907502b10e579e3a20e85fac08673f01c7a4cf9e6decfbdf6851b5baefb72`
  - submit: `0xa5205425f9bd22f61537fcb1442071a461de2d740b338b0aa3bbe8bd06de6367`
  - seal: `0x395322f33fceb198dec018f6bc0d6a0db3cf07ca6aa50302f76bd2b70040549c`
  - evaluate: `0x77319914dbbccb4122b19e206dfbfb1d95bd7561dbc0e0c7f53f722ab42f02fb`
- Independent Python SDK readback exactly matches accepted browser evaluation output. Original ambiguous UI separately displays REJECTED and its expanded JSON equals the captured live on-chain result.
- New failures preserved: initial focused run stopped on HTTP 502 while polling a submission; resumed the saved hash without resending it. The read-only UI probe initially waited for a hidden `<pre>` inside closed `<details>`; corrected to wait for attachment and expand the panel, then passed. Both tracebacks remain in their logs. These are harness/transport failures, not contract changes.

Evidence: `forensic-original.json` (fresh primary receipts and original round), `forensic-live.json` (18 writes, 3 rounds, full receipts/readbacks), `forensic-browser.json`, `forensic-summary.json` (independent browser readback and original metadata binding), corresponding `.log` files, and `forensic-browser.png` / `forensic-original-ui.png` in `evidence/`. Original evidence files were not overwritten. The only existing harness edit adds a screenshot-path environment override to preserve the historical screenshot. Contract, frontend application, pinned proposals and original failed smoke are unchanged.

**REJECTED is mechanically correct and a defensible ineligibility decision for a proposal explicitly lacking required deliverables. It is not proof that the model's DISTINCT rationale obeyed the ambiguity instruction.** No contract change or redeployment is required for the demonstrated mapping issue. Review must not promise that all vague proposals yield INCONCLUSIVE or that unanimous validators approved this result. The updated demo claim is conservative allocation under nondeterministic interpretation, not guaranteed exact labels. Three successful repetitions support demo repeatability; they do not prove universal model determinism.

Remaining reviewer/Steward risks: semantic rationale/label inconsistency remains possible; minority disagreement is real; no application appeal; testnet/provider outages; direct-mode mocks do not reproduce network consensus; no GLSim/Bradbury coverage; original `gw-integrity` scenario remains unexecuted live. This investigation does not convert those skipped scenarios into passes. If reviewers require a categorical guarantee that semantic vagueness must always persist INCONCLUSIVE, that stronger requirement is NOT met by this implementation and would require a separately specified change and renewed deployment authorization.

Scoped final status: READY FOR PORTAL REVIEW as the disclosed testnet prototype, not production certification or an exact-label guarantee. No portal submission, git push, frontend deployment or contract redeployment was performed during the forensic phase. Subsequent publication is documented separately in PUBLIC_RELEASE.md.


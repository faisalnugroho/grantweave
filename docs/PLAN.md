# GrantWeave — Project build, September 2026

Scope: complete testnet project, not Portal submission. No real funds. Budget units are allocation credits, not GEN payouts. New domain: semantic duplicate-funding prevention for public-goods grants, not code/license/wallet audit.

Architecture: owner creates a bounded round with natural-language rubric and budget; anyone submits a pinned public proposal (raw.githubusercontent.com/<owner>/<repo>/<40-char SHA>/<path>, sha256 exact body); owner seals submissions. Permissionless sequential adjudication in submission order compares proposal scope against already RESERVED proposals in this round. LLM labels rubric eligibility PASS/FAIL/UNCERTAIN and duplication DISTINCT/DUPLICATE/UNCERTAIN with grounded quotes; contract derives RESERVED/REJECTED/INCONCLUSIVE/OVER_BUDGET and decrements allocation budget only for RESERVED. All evidence bounded, complete or fail-closed; byte commitments compared in validator; no caller-supplied decisions. Unknown evidence never reserves. Source documents public, may be self-authored, hash proves integrity not truth. No global duplicate detection claim. No payment, legal binding, or identity proof. No appeal in v1: terminal records immutable; new round required. Submission ordering disclosed.

Shared API (all writes return None; views JSON string):
create_round(round_id: str, title: str, rubric: str, budget: int)
submit_proposal(round_id: str, title: str, url: str, digest: str, amount: int)
seal_round(round_id: str)
evaluate_next(round_id: str)
get_round(round_id: str) -> str
list_rounds() -> str (JSON list of IDs)
get_round returns {id,title,rubric,budget,remaining,owner,sealed,next_index,proposals:[{index,title,url,digest,amount,applicant,status,result}]}.
Statuses PENDING, RESERVED, REJECTED, INCONCLUSIVE, OVER_BUDGET.
Result evidence details provided by contract, frontend renders JSON safely.

Workstreams:
1. Contract + real gltest Direct-mode suite with adversarial cases.
2. Static functional dashboard, fresh testnet burner, SDK writes/readback, responsive and clear testnet boundary.
3. Spec review then independent security review, regressions, actual test/lint runs.
4. Testnet deployment + live smoke when infrastructure available; honest evidence fixtures labeled synthetic examples.
5. Public repository/Pages, browser verification, README/audit/submission draft (category Project), evidence bundle.

No fabricated test output, no portal submission, no interaction with other existing project state.

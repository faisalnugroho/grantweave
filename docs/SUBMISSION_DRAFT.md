# Portal submission draft — submit manually as Project

Title: GrantWeave — distinct-work allocation desk
Category: Project
Suggested primary tag: Governance
Suggested secondary tags: Proposal Screening; Treasury Allocation
Network: studio (Studionet, chain 61999)

## Description (under 1000 characters)
GrantWeave is a public-goods allocation desk that uses GenLayer validators to judge whether a proposal meets a round's rubric and describes distinct work rather than rephrasing earlier reserved deliverables. Applicants submit commit-pinned public text with SHA-256; validators fetch it, check byte integrity, interpret scope and cite every source. The contract derives the outcome and reserves bounded allocation credits only for eligible, distinct work within budget. Includes a usable dashboard, 109 direct-mode tests (including 12 forensic regressions), GenVM validation, first-party security review, real multi-validator transactions and browser-to-chain verification. This is a testnet prototype: credits are not payouts, comparison is within-round only, open admission is not Sybil-resistant, and LLM judgments can be wrong. One observed consensus disagreement and its retry are disclosed in the verification report.

## Links
Repository: https://github.com/faisalnugroho/grantweave
Dashboard: https://faisalnugroho.github.io/grantweave/
Contract: https://explorer-studio.genlayer.com/contracts/0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466
Verification: https://github.com/faisalnugroho/grantweave/blob/main/docs/VERIFICATION.md
Audit: https://github.com/faisalnugroho/grantweave/blob/main/docs/AUDIT.md
Consensus forensic report: https://github.com/faisalnugroho/grantweave/blob/main/docs/CONSENSUS_FORENSIC.md
Public release report: https://github.com/faisalnugroho/grantweave/blob/main/docs/PUBLIC_RELEASE.md

## Demonstration evidence
Distinct: https://explorer-studio.genlayer.com/tx/0x4e9ac5eeafa613e6ea5756a885c5674ef908352a34908c1f6289c842845b0999
Duplicate rejected: https://explorer-studio.genlayer.com/tx/0x01d36aab387f07adb3a55efcc250e371ebd77f37dccb36eed1f563691d13ee52
Over budget: https://explorer-studio.genlayer.com/tx/0x6a7a4a174e52df9e5d043b5431b351a0ada3c29f07e67ad8ea8bfac23057fa63
Ineligible rejected: https://explorer-studio.genlayer.com/tx/0xd15304c5cea29d90d4e9252e800dd481b8c04f6ed9b8dfda4b6c7be04fd4862b
Public dashboard evaluate: https://explorer-studio.genlayer.com/tx/0x2311bc9976660ccdefc95a05c059148f526698981cddf5f116ee51389905958d
Complete pipeline evaluate: https://explorer-studio.genlayer.com/tx/0x5afc4f096b5ff72e3076ade034a8eaf57e6b7ffa3b6e3d29f46e8fedb02049da

## Honest scope notes
The project is new work in the week September 14–20, 2026; it is not a reuse of the previous code/license/wallet audit domains. Do not claim ecosystem-wide uniqueness or guaranteed Portal acceptance.
No real-world grants or users are claimed; examples are synthetic. First-party audit only, not an external auditor endorsement. The initial ambiguous proposal failed consensus, then retry was REJECTED rather than the harness's expected INCONCLUSIVE. Hash-mismatch live scenario was not run. No full-smoke-all-green or mainnet readiness claim.

The owner submits this Project. No login, signature, review or submission action has been performed in the Portal.

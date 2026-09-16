# GrantWeave

A GenLayer public-goods allocation desk: judge whether a proposal is eligible and funds genuinely distinct deliverables rather than rephrasing work already reserved in the same round.

Status: development and verification in progress. Not submitted to the Portal.

## Boundaries
- Allocation credits only: no GEN custody, payments or proof of real-world funding.
- Compares against earlier RESERVED proposals in THIS round only; not a global grant database.
- Submission order has priority; the round creator controls sealing.
- Hash-pinned public documents prove byte integrity, not ownership, identity or truth.
- LLM judgments can be wrong; no correctness guarantee or independent professional audit.
- v1 terminal decisions have no appeal; create a new round for a revised assessment.
- Demonstration evidence in examples/ is explicitly synthetic, not real grant applications.

## Local tests
Python 3.12; install requirements-dev.txt and run `python -m pytest tests/ -v`. SDK runner setup instructions and complete verification evidence will be added after execution.

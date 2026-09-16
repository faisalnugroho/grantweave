import copy
import json
from test_contract import evaluate, get, submit, mocks, model, BODIES, c


def test_uncertain_reason_may_differ(c, direct_vm):
    record = evaluate(c, direct_vm, model([BODIES[0]], 'UNCERTAIN', 'UNCERTAIN'))
    proposed = copy.deepcopy(record['proposals'][0]['result'])
    proposed['reason'] = 'An independent explanation of why evidence does not establish eligibility.'
    assert direct_vm.run_validator(leader_result=proposed)


def test_uncertain_cannot_drop_grounding(c, direct_vm):
    record = evaluate(c, direct_vm, model([BODIES[0]], 'UNCERTAIN', 'UNCERTAIN'))
    proposed = copy.deepcopy(record['proposals'][0]['result'])
    proposed['citations'] = []
    assert not direct_vm.run_validator(leader_result=proposed)


def test_failsafe_rejects_unbounded_or_extra_fields(c, direct_vm):
    submit(c)
    c.seal_round('test-round')
    c.evaluate_next('test-round')
    honest = get(c)['proposals'][0]['result']
    assert direct_vm.run_validator(leader_result=honest)
    for field, value in [('reason', 'x' * 1001), ('reason', None), ('allocation', 1000000)]:
        proposed = copy.deepcopy(honest)
        proposed[field] = value
        assert not direct_vm.run_validator(leader_result=proposed)

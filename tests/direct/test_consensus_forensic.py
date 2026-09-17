"""Replay captured live outputs; these are NOT live LLM tests."""
import copy
import json
import re
import sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from consensus_invariant import decode_output, check_binding, check_ambiguous
from live_smoke import succeeded

CAPTURE = json.loads((ROOT / 'evidence/forensic-original.json').read_text())
ROUND = CAPTURE['round']


def replay(direct_deploy, vm, final_output):
    c = direct_deploy('contracts/grantweave.py')
    c.create_round('gw-overlap', ROUND['title'], ROUND['rubric'], ROUND['budget'])
    for p in ROUND['proposals']:
        c.submit_proposal('gw-overlap', p['title'], p['url'], p['digest'], p['amount'])
    c.seal_round('gw-overlap')
    for i, p in enumerate(ROUND['proposals']):
        vm.clear_mocks()
        for entry in ROUND['proposals']:
            body = (ROOT / 'examples' / entry['url'].rsplit('/', 1)[1]).read_text()
            vm.mock_web(re.escape(entry['url']) + '$', {'status': 200, 'body': body})
        vm.mock_llm('.*', json.dumps(final_output if i == 4 else p['result']))
        c.evaluate_next('gw-overlap')
    return c


def test_live_fail_distinct_replays_as_rejected(direct_deploy, direct_vm):
    """Confirmed FAIL+DISTINCT has no uncertain label: branch 204, not 202."""
    output = decode_output(CAPTURE['transactions']['retry']['tx'])
    c = replay(direct_deploy, direct_vm, output)
    record = json.loads(c.get_round('gw-overlap'))
    assert record['proposals'][4]['result'] == output
    assert record['proposals'][4]['status'] == 'REJECTED'
    assert record['remaining'] == 20 and record['next_index'] == 5
    assert direct_vm.run_validator()
    with direct_vm.expect_revert('round_complete'):
        c.evaluate_next('gw-overlap')


@pytest.mark.parametrize('change', ['uncertain_duplication', 'missing_eligibility', 'missing_baseline_quote'])
def test_ambiguous_or_incomplete_response_is_not_rejected(direct_deploy, direct_vm, change):
    output = copy.deepcopy(ROUND['proposals'][4]['result'])
    if change == 'uncertain_duplication':
        output['duplication'] = 'UNCERTAIN'
    elif change == 'missing_eligibility':
        del output['eligibility']
    else:
        output['citations'] = output['citations'][:1]
    c = replay(direct_deploy, direct_vm, output)
    record = json.loads(c.get_round('gw-overlap'))
    assert record['proposals'][4]['status'] == 'INCONCLUSIVE'
    assert record['remaining'] == 20
    assert direct_vm.run_validator()


def test_validator_disagreement_cannot_validate_live_rejection(direct_deploy, direct_vm):
    independent = copy.deepcopy(ROUND['proposals'][4]['result'])
    independent['duplication'] = 'UNCERTAIN'
    replay(direct_deploy, direct_vm, independent)
    assert not direct_vm.run_validator(leader_result=ROUND['proposals'][4]['result'])


def test_original_failure_preserved_and_retry_bound_to_request():
    original = CAPTURE['transactions']['original']['tx']
    retry = CAPTURE['transactions']['retry']['tx']
    assert not succeeded(original)
    assert sum(v == 'agree' for v in original['consensus_data']['votes'].values()) == 2
    assert succeeded(retry)
    bodies = [(ROOT/'examples'/name).read_bytes() for name in ['ambiguous.md', 'open-map.md']]
    output = check_binding(retry, ROUND, 4, bodies, CAPTURE['address'])
    assert output['eligibility'] == 'FAIL' and output['duplication'] == 'DISTINCT'
    assert decode_output(original)['hashes'] == output['hashes']


@pytest.mark.parametrize('mutation', ['wrong_request', 'wrong_result', 'minority'])
def test_binding_assertions_are_red_capable(mutation):
    tx = copy.deepcopy(CAPTURE['transactions']['retry']['tx'])
    record = copy.deepcopy(ROUND)
    if mutation == 'wrong_request':
        record['id'] = 'another-round'
    elif mutation == 'wrong_result':
        record['proposals'][4]['result']['reason'] = 'Another judgment, not the actual accepted output.'
    else:
        for k in list(tx['consensus_data']['votes'])[1:]:
            tx['consensus_data']['votes'][k] = 'disagree'
    with pytest.raises(AssertionError):
        check_binding(tx, record, 4, [(ROOT/'examples'/n).read_bytes() for n in ['ambiguous.md','open-map.md']], CAPTURE['address'])


@pytest.mark.parametrize('status', ['RESERVED', 'REJECTED', 'INCONCLUSIVE'])
def test_nonallocation_invariant_keeps_distinct_semantics(status):
    after = copy.deepcopy(ROUND)
    before = copy.deepcopy(ROUND)
    before['next_index'] = 4
    before['proposals'][4].update(status='PENDING', result={})
    after['proposals'][4]['status'] = status
    # Captured labels are FAIL/DISTINCT, so claiming INCONCLUSIVE is also wrong.
    if status == 'REJECTED':
        check_ambiguous(before, after, 4)
    else:
        with pytest.raises(AssertionError):
            check_ambiguous(before, after, 4)

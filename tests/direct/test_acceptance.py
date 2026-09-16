import hashlib
import json
import re

URL = 'https://raw.githubusercontent.com/example/grants/' + 'a' * 40 + '/proposal.md'
BODY = 'Publish an openly licensed beginner manual for public mapping, free to everyone within four weeks.'
RUBRIC = 'Fund concrete openly licensed public goods with freely accessible deliverables and a clear timeline.'


def test_allocation_reserves_exactly_once(direct_vm, direct_deploy):
    contract = direct_deploy('contracts/grantweave.py')
    contract.create_round('acceptance', 'Acceptance round', RUBRIC, 100)
    contract.submit_proposal('acceptance', 'Public mapping manual', URL, hashlib.sha256(BODY.encode()).hexdigest(), 40)
    contract.seal_round('acceptance')
    direct_vm.mock_web(re.escape(URL) + '$', {'status': 200, 'body': BODY})
    direct_vm.mock_llm('.*', json.dumps({'eligibility': 'PASS', 'duplication': 'DISTINCT', 'reason': 'Clear open documentation scope with a four-week delivery timeline.', 'citations': [{'source': 0, 'quote': BODY}]}))
    contract.evaluate_next('acceptance')
    record = json.loads(contract.get_round('acceptance'))
    assert record['proposals'][0]['status'] == 'RESERVED', record
    assert record['remaining'] == 60
    assert record['next_index'] == 1
    assert direct_vm.run_validator()
    with direct_vm.expect_revert('round_complete'):
        contract.evaluate_next('acceptance')
    assert json.loads(contract.get_round('acceptance'))['remaining'] == 60

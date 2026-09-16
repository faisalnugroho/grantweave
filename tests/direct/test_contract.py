"""Real GenVM direct-mode tests; web/LLM boundaries are explicitly mocked."""
import copy
import hashlib
import json
import re
import pytest

BASE = 'https://raw.githubusercontent.com/example/grants/' + 'a' * 40 + '/'
RUBRIC = 'Fund concrete openly licensed public goods with freely accessible deliverables and a clear timeline.'
BODIES = [
    'Publish an openly licensed mapping manual, free to everyone, with twelve runnable examples in four weeks.',
    'Publish an openly licensed audio guide to historical archives, freely accessible in three weeks.',
    'Publish a freely accessible guide to open astronomy datasets with a permissive license within six weeks.',
]


def digest(body):
    return hashlib.sha256(body.encode() if isinstance(body, str) else body).hexdigest()


def get(c):
    return json.loads(c.get_round('test-round'))


@pytest.fixture
def c(direct_deploy):
    obj = direct_deploy('contracts/grantweave.py')
    obj.create_round('test-round', 'Public goods', RUBRIC, 100)
    return obj


def submit(c, index=0, amount=40, body=None, sha=None):
    body = body or BODIES[index % len(BODIES)]
    url = BASE + str(index) + '.md'
    c.submit_proposal('test-round', 'Proposal ' + str(index), url, sha or digest(body), amount)
    return url


def model(bodies, eligibility='PASS', duplication='DISTINCT'):
    return {'eligibility': eligibility, 'duplication': duplication,
            'reason': 'The proposal meets the public-goods rubric with a concrete, distinct scope.',
            'citations': [{'source': i, 'quote': b} for i, b in enumerate(bodies)]}


def mocks(vm, index=0, output=None, bodies=None, status=200):
    vm.clear_mocks()
    bodies = bodies or [BODIES[index]]
    vm.mock_web(re.escape(BASE + str(index) + '.md') + '$', {'status': status, 'body': bodies[0]})
    for i, body in enumerate(bodies[1:]):
        vm.mock_web(re.escape(BASE + str(i) + '.md') + '$', {'status': 200, 'body': body})
    vm.mock_llm('.*', json.dumps(model(bodies) if output is None else output))


def evaluate(c, vm, output=None, status=200):
    submit(c)
    c.seal_round('test-round')
    mocks(vm, output=output, status=status)
    c.evaluate_next('test-round')
    return get(c)


@pytest.mark.parametrize('field,value,reason', [
    ('id', '', 'invalid_round_id'), ('id', '../escape', 'invalid_round_id'),
    ('id', 'XyZ', 'invalid_round_id'), ('id', 'a' * 41, 'invalid_round_id'),
    ('title', '  ', 'invalid_title'), ('title', 'a' * 121, 'invalid_title'),
    ('rubric', 'tiny', 'invalid_rubric'), ('rubric', 'a' * 2001, 'invalid_rubric'),
    ('budget', 0, 'invalid_budget'), ('budget', -1, 'invalid_budget'),
    ('budget', 1000000001, 'invalid_budget'),
])
def test_round_input_validation(c, direct_vm, field, value, reason):
    args = {'id': 'new-round', 'title': 'Valid title', 'rubric': RUBRIC, 'budget': 100}
    args[field] = value
    with direct_vm.expect_revert(reason):
        c.create_round(*args.values())


def test_round_duplicate_and_listing(c, direct_vm):
    assert json.loads(c.list_rounds()) == ['test-round']
    with direct_vm.expect_revert('round_exists'):
        c.create_round('test-round', 'Other title', RUBRIC, 100)
    with direct_vm.expect_revert('round_not_found'):
        c.get_round('missing')


@pytest.mark.parametrize('url', [
    'http://localhost/test.md', 'https://127.0.0.1/test.md',
    'https://raw.githubusercontent.com.evil.test/a/b/' + 'a'*40 + '/x.md',
    'https://raw.githubusercontent.com/a/b/main/x.md',
    BASE + '../secret.md', BASE + './x.md', BASE + 'a//x.md',
    BASE + '%2e%2e/x.md', BASE + 'x.md?query=1', BASE + 'x.md#frag',
    BASE + 'x.json', BASE + 'x.md\n', 'https://user@raw.githubusercontent.com/a/b/' + 'a'*40 + '/x.md',
])
def test_url_allowlist(c, direct_vm, url):
    with direct_vm.expect_revert('invalid_'):
        c.submit_proposal('test-round', 'Valid title', url, digest(BODIES[0]), 20)


@pytest.mark.parametrize('amount', [0, -1, 101, 1000000000000000000])
def test_invalid_amount(c, direct_vm, amount):
    with direct_vm.expect_revert('invalid_amount'):
        submit(c, amount=amount)


@pytest.mark.parametrize('sha', ['abc', 'A' * 64, 'g' * 64, 'a' * 63, 'a' * 65])
def test_invalid_digest(c, direct_vm, sha):
    with direct_vm.expect_revert('invalid_digest'):
        submit(c, sha=sha)


def test_duplicate_body_rejected(c, direct_vm):
    submit(c)
    with direct_vm.expect_revert('duplicate_digest'):
        submit(c, index=1, body=BODIES[0])


def test_capacity(c, direct_vm):
    for i in range(8):
        submit(c, i, body=BODIES[0] + str(i))
    with direct_vm.expect_revert('round_full'):
        submit(c, 9, body=BODIES[0] + '9')


def test_seal_permissions_and_transitions(c, direct_vm, direct_bob):
    with direct_vm.expect_revert('empty_round'):
        c.seal_round('test-round')
    submit(c)
    with direct_vm.expect_revert('round_not_sealed'):
        c.evaluate_next('test-round')
    with direct_vm.prank(direct_bob):
        with direct_vm.expect_revert('owner_only'):
            c.seal_round('test-round')
    c.seal_round('test-round')
    with direct_vm.expect_revert('round_sealed'):
        c.seal_round('test-round')
    with direct_vm.expect_revert('round_sealed'):
        submit(c, 1)


@pytest.mark.parametrize('eligibility,duplication,status', [
    ('PASS', 'DISTINCT', 'RESERVED'), ('FAIL', 'DISTINCT', 'REJECTED'),
    ('PASS', 'DUPLICATE', 'REJECTED'), ('FAIL', 'DUPLICATE', 'REJECTED'),
    ('UNCERTAIN', 'DISTINCT', 'INCONCLUSIVE'), ('PASS', 'UNCERTAIN', 'INCONCLUSIVE'),
    ('FAIL', 'UNCERTAIN', 'INCONCLUSIVE'), ('UNCERTAIN', 'DUPLICATE', 'INCONCLUSIVE'),
    ('UNCERTAIN', 'UNCERTAIN', 'INCONCLUSIVE'),
])
def test_decision_matrix(c, direct_vm, eligibility, duplication, status):
    record = evaluate(c, direct_vm, model([BODIES[0]], eligibility, duplication))
    assert record['proposals'][0]['status'] == status
    assert record['remaining'] == (60 if status == 'RESERVED' else 100)


@pytest.mark.parametrize('field,value', [
    ('eligibility', 'APPROVED'), ('duplication', 'NEW'), ('reason', ''),
    ('reason', 'x' * 1001), ('reason', 12), ('citations', []), ('citations', None),
    ('citations', [{'source': 0, 'quote': 'not a grounded quote from any actual source'}]),
    ('citations', [{'source': -1, 'quote': BODIES[0]}]),
    ('citations', [{'source': 1, 'quote': BODIES[0]}]),
    ('citations', [{'source': '0', 'quote': BODIES[0]}]),
    ('citations', [{'source': False, 'quote': BODIES[0]}]),
    ('citations', [{'source': 0, 'quote': 'short'}]),
    ('citations', ['not a dict']),
])
def test_malformed_model_fail_closed(c, direct_vm, field, value):
    output = model([BODIES[0]])
    output[field] = value
    record = evaluate(c, direct_vm, output)
    assert record['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert record['remaining'] == 100


@pytest.mark.parametrize('output', [[], 'not-json', 10, True, {'winner': 'alice'}, {'eligibility': 'PASS'}])
def test_wrong_model_shape(c, direct_vm, output):
    record = evaluate(c, direct_vm, output)
    assert record['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert record['remaining'] == 100


@pytest.mark.parametrize('status', [201, 301, 400, 403, 404, 429, 500])
def test_http_status_failure(c, direct_vm, status):
    record = evaluate(c, direct_vm, status=status)
    assert record['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert record['remaining'] == 100


@pytest.mark.parametrize('body', ['tiny', 'x' * 12001, b'\xff' * 25])
def test_source_bounds_and_encoding(c, direct_vm, body):
    url = submit(c, body=body)
    c.seal_round('test-round')
    direct_vm.mock_web(re.escape(url) + '$', {'status': 200, 'body': body})
    direct_vm.mock_llm('.*', json.dumps(model([BODIES[0]])))
    c.evaluate_next('test-round')
    assert get(c)['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert get(c)['remaining'] == 100


def test_hash_mismatch_clamps_good_model(c, direct_vm):
    submit(c, sha='0' * 64)
    c.seal_round('test-round')
    mocks(direct_vm)
    c.evaluate_next('test-round')
    assert get(c)['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert get(c)['remaining'] == 100


def test_no_web_and_no_model_fail_closed(c, direct_vm):
    submit(c)
    c.seal_round('test-round')
    c.evaluate_next('test-round')
    assert get(c)['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert get(c)['remaining'] == 100


def test_model_exception(c, direct_vm):
    url = submit(c)
    c.seal_round('test-round')
    direct_vm.mock_web(re.escape(url), {'status': 200, 'body': BODIES[0]})
    c.evaluate_next('test-round')
    assert get(c)['proposals'][0]['status'] == 'INCONCLUSIVE'


def test_baseline_comparison_budget_and_rejection(c, direct_vm, direct_bob):
    for i, amount in enumerate([60, 30, 50]):
        submit(c, i, amount)
    c.seal_round('test-round')
    with direct_vm.prank(direct_bob):
        mocks(direct_vm)
        c.evaluate_next('test-round')
    assert get(c)['remaining'] == 40
    mocks(direct_vm, 1, bodies=[BODIES[1], BODIES[0]], output=model([BODIES[1], BODIES[0]], duplication='DUPLICATE'))
    c.evaluate_next('test-round')
    assert get(c)['proposals'][1]['status'] == 'REJECTED'
    mocks(direct_vm, 2, bodies=[BODIES[2], BODIES[0]])
    c.evaluate_next('test-round')
    record = get(c)
    assert [p['status'] for p in record['proposals']] == ['RESERVED', 'REJECTED', 'OVER_BUDGET']
    assert record['remaining'] == 40
    assert sum(p['amount'] for p in record['proposals'] if p['status'] == 'RESERVED') + record['remaining'] == record['budget']
    assert direct_vm.run_validator()


def test_missing_baseline_quote_fails_closed(c, direct_vm):
    submit(c)
    submit(c, 1)
    c.seal_round('test-round')
    mocks(direct_vm)
    c.evaluate_next('test-round')
    mocks(direct_vm, 1, bodies=[BODIES[1], BODIES[0]], output=model([BODIES[1]]))
    c.evaluate_next('test-round')
    assert get(c)['proposals'][1]['status'] == 'INCONCLUSIVE'
    assert get(c)['remaining'] == 60


def test_validator_rejects_divergent_evidence(c, direct_vm):
    record = evaluate(c, direct_vm)
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(BASE + '0.md'), {'status': 200, 'body': BODIES[1]})
    direct_vm.mock_llm('.*', json.dumps(model([BODIES[1]])))
    assert not direct_vm.run_validator(leader_result=record['proposals'][0]['result'])


@pytest.mark.parametrize('field,value', [
    ('eligibility', 'FAIL'), ('duplication', 'DUPLICATE'), ('hashes', ['0'*64]),
    ('citations', []), ('reason', ''), ('reason', 'x'*1001),
    ('citations', [{'source': 0, 'quote': 'invented source quotation for the allocation'}]),
])
def test_validator_rejects_tampered_result(c, direct_vm, field, value):
    record = evaluate(c, direct_vm)
    proposed = copy.deepcopy(record['proposals'][0]['result'])
    assert direct_vm.run_validator(leader_result=proposed)
    proposed[field] = value
    assert not direct_vm.run_validator(leader_result=proposed)


def test_validator_allows_different_grounded_reason(c, direct_vm):
    record = evaluate(c, direct_vm)
    proposed = copy.deepcopy(record['proposals'][0]['result'])
    proposed['reason'] = 'The public mapping manual is a concrete, freely accessible deliverable.'
    assert direct_vm.run_validator(leader_result=proposed)


def test_model_cannot_set_amount_or_final_status(c, direct_vm):
    output = model([BODIES[0]])
    output.update({'amount': 1000000, 'remaining': 999999, 'status': 'RESERVED'})
    record = evaluate(c, direct_vm, output)
    assert record['remaining'] == 60
    assert record['proposals'][0]['amount'] == 40
    assert 'amount' not in record['proposals'][0]['result']

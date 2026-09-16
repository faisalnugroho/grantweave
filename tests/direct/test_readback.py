import json
from test_contract import c, submit, mocks, get


def test_missing_integrity_round_is_not_corrupt_storage(c, direct_vm):
    assert 'gw-integrity' not in json.loads(c.list_rounds())
    with direct_vm.expect_revert('round_not_found'):
        c.get_round('gw-integrity')
    assert get(c)['remaining'] == 100


def test_created_integrity_record_serializes_after_failed_hash(c, direct_vm):
    submit(c, sha='0' * 64)
    c.seal_round('test-round')
    mocks(direct_vm)
    c.evaluate_next('test-round')
    record = get(c)
    assert json.loads(json.dumps(record)) == record
    assert record['proposals'][0]['status'] == 'INCONCLUSIVE'
    assert record['remaining'] == 100

"""Focused smoke assertions. Does not decide contract outcomes or submit writes."""
import base64
import hashlib
from genlayer_py.abi import calldata


def decode_output(tx):
    raw = base64.b64decode(tx['consensus_data']['leader_receipt'][0]['eq_outputs']['0'])
    assert raw[0] == 0, 'nondeterministic block did not return'
    value = calldata.decode(raw[1:])
    assert isinstance(value, dict)
    return value


def check_binding(tx, record, index, bodies, address):
    assert tx['recipient'].lower() == address.lower()
    assert calldata.decode(base64.b64decode(tx['data']['calldata'])) == {'method': 'evaluate_next', 'args': [record['id']]}
    assert tx['leader_only'] is False
    assert tx['status'] == 'FINALIZED' and tx['result_name'] == 'MAJORITY_AGREE'
    consensus = tx['consensus_data']
    leader = consensus['leader_receipt'][0]
    assert leader['execution_result'] == 'SUCCESS'
    votes = consensus['votes']
    assert len(votes) == tx['num_of_initial_validators']
    assert sum(v == 'agree' for v in votes.values()) > len(votes) // 2
    receipts = consensus['leader_receipt'][1:] + consensus['validators']
    agreeing = {v['node_config']['address']: v for v in receipts if v.get('vote') == 'agree'}
    assert set(agreeing) == {k for k, v in votes.items() if v == 'agree'}
    assert all(v['execution_result'] == 'SUCCESS' and v['contract_state_hash'] == leader['contract_state_hash'] for v in agreeing.values())
    p = record['proposals'][index]
    entries = [p] + [x for x in record['proposals'][:index] if x['status'] == 'RESERVED']
    result = decode_output(tx)
    assert result == p['result'], 'persisted result differs from accepted output'
    assert len(bodies) == len(entries)
    for entry, body in zip(entries, bodies):
        assert hashlib.sha256(body).hexdigest() == entry['digest']
    hashes = [entry['digest'] for entry in entries]
    if result['citations']:
        assert result['hashes'] == hashes
        assert {c['source'] for c in result['citations']} == set(range(len(entries)))
        for c in result['citations']:
            assert 20 <= len(c['quote']) <= 500
            assert c['quote'] in bodies[c['source']].decode('utf-8')
    else:
        assert result['eligibility'] == result['duplication'] == 'UNCERTAIN'
    assert record['remaining'] + sum(x['amount'] for x in record['proposals'] if x['status'] == 'RESERVED') == record['budget']
    return result


def check_ambiguous(before, after, index):
    """Vague request must never allocate; labels retain distinct meanings."""
    p = after['proposals'][index]
    result = p['result']
    assert p['status'] in ('INCONCLUSIVE', 'REJECTED'), 'vague request must not allocate'
    assert after['remaining'] == before['remaining']
    assert after['next_index'] == before['next_index'] + 1 == index + 1
    assert after['proposals'][:index] == before['proposals'][:index]
    assert {k:v for k,v in p.items() if k not in ('status','result')} == {k:v for k,v in before['proposals'][index].items() if k not in ('status','result')}
    if p['status'] == 'INCONCLUSIVE':
        assert 'UNCERTAIN' in (result['eligibility'], result['duplication'])
    else:
        assert result['eligibility'] in ('PASS', 'FAIL')
        assert result['duplication'] in ('DISTINCT', 'DUPLICATE')
        assert result['eligibility'] == 'FAIL' or result['duplication'] == 'DUPLICATE'

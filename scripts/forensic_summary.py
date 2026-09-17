"""Read-only summary of original evidence and fresh browser calldata/readback."""
import base64
import json
from pathlib import Path
import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.abi import calldata
from live_smoke import ROOT, KEY, rpc, succeeded
from consensus_invariant import decode_output, check_binding

original = json.loads((ROOT/'evidence/forensic-original.json').read_text())
record = original['round']
report = {'address':original['address'], 'source_sha256':original['source_sha256'], 'original':{}}
for label in ('original','retry'):
    item = original['transactions'][label]
    tx = item['tx']
    report['original'][label] = {'hash':tx['hash'], 'status':tx['status'], 'result_name':tx['result_name'], 'decoded':item['decoded'], 'votes':tx['consensus_data']['votes'], 'output':decode_output(tx), 'history_status_changes':[x['status_changes'] for x in tx['consensus_history']['consensus_results']]}
    assert item['decoded'] == {'method':'evaluate_next','args':['gw-overlap']}
    assert tx['recipient'] == original['address']
# Bind round configuration + all immutable proposal metadata to accepted calldata.
for label, item in original['transactions'].items():
    args = item['decoded']['args']
    if item['decoded']['method'] == 'create_round':
        assert args == [record['id'], record['title'], record['rubric'], record['budget']]
    if item['decoded']['method'] == 'submit_proposal':
        p = next(p for p in record['proposals'] if p['url'] == args[2])
        assert args == [record['id'],p['title'],p['url'],p['digest'],p['amount']]
        assert p['applicant'] == item['tx']['from_address']
        assert succeeded(item['tx'])
report['original']['submission_calldata_matches'] = True
report['original']['retry_output_equals_persisted'] = decode_output(original['transactions']['retry']['tx']) == record['proposals'][4]['result']
assert report['original']['retry_output_equals_persisted']
account = create_account(account_private_key=json.loads(KEY.read_text())['private_key'])
client = create_client(chain=studionet, account=account)
browser = json.loads((ROOT/'evidence/forensic-browser.json').read_text())
assert browser['pass']
readback = json.loads(client.read_contract(address=original['address'],function_name='get_round',args=[browser['round_id']]))
assert readback['proposals'][0]['status'] == 'RESERVED' and readback['remaining'] == 60
transactions = []
for step in browser['steps']:
    txhash = step['transaction'].split()[1]
    tx = rpc('eth_getTransactionByHash',[txhash])
    decoded = calldata.decode(base64.b64decode(tx['data']['calldata']))
    assert succeeded(tx) and tx['recipient'] == original['address']
    assert decoded['method'] == step['label'] and decoded['args'][0] == browser['round_id']
    transactions.append({'tx':tx,'decoded':decoded})
assert len({item['tx']['hash'] for item in transactions}) == 4
p = readback['proposals'][0]
assert transactions[1]['decoded']['args'] == [readback['id'],p['title'],p['url'],p['digest'],p['amount']]
body = requests.get(p['url'],timeout=45); body.raise_for_status()
check_binding(transactions[-1]['tx'],readback,0,[body.content],original['address'])
report['browser'] = {'readback':readback,'transactions':transactions,'verified':True}
(ROOT/'evidence/forensic-summary.json').write_text(json.dumps(report,indent=2))
print('ORIGINAL_BINDING_AND_BROWSER_READBACK_PASS',browser['round_id'])

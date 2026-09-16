"""Read-only authoritative verification; never creates accounts or transactions."""
import base64
import hashlib
import json
from pathlib import Path
import requests
import subprocess
from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet
from genlayer_py.abi import calldata
ROOT = Path(__file__).resolve().parents[1]
log = json.loads((ROOT / 'evidence/live.json').read_text())
key = json.loads((Path.home()/'.genlayer-keys/grantweave-key.json').read_text())
client = create_client(chain=studionet, account=create_account(account_private_key=key['private_key']))
report = {'address':log['address'], 'read_only':True}
ids = json.loads(client.read_contract(address=log['address'], function_name='list_rounds', args=[]))
report['rounds'] = {}
for rid in ids:
    value = client.read_contract(address=log['address'], function_name='get_round', args=[rid])
    assert isinstance(value, str)
    record = json.loads(value)
    assert record['id'] == rid
    assert record['budget'] == record['remaining'] + sum(p['amount'] for p in record['proposals'] if p['status'] == 'RESERVED')
    report['rounds'][rid] = record
    print(rid, 'remaining', record['remaining'], 'next', record['next_index'], [p['status'] for p in record['proposals']])
report['integrity_round_exists'] = 'gw-integrity' in ids
r = requests.post(log['rpc'],json={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionByHash','params':[log['deploy_tx']]},timeout=30)
r.raise_for_status()
tx = r.json()['result']
source = base64.b64decode(tx['data']['contract_code'])
report['deployed_source_matches_repo'] = source == (ROOT/'contracts/grantweave.py').read_bytes()
report['source_sha256'] = hashlib.sha256(source).hexdigest()
assert report['deployed_source_matches_repo']
# Recover browser transaction labels from actual calldata, not DOM timing.
url = 'https://explorer-studio.genlayer.com/api/transactions?address=' + log['address'] + '&limit=100'
response = subprocess.run(['curl', '-fLsS', '--max-time', '45', '-A', 'Mozilla/5.0', url], capture_output=True, check=True, text=True)
report['browser_transactions'] = []
for item in json.loads(response.stdout)['transactions']:
    raw = (item.get('data') or {}).get('calldata')
    if not raw:
        continue
    decoded = calldata.decode(base64.b64decode(raw))
    args = decoded.get('args', [])
    if args and isinstance(args[0], str) and args[0].startswith('browser-'):
        report['browser_transactions'].append({'hash':item['hash'],'status':item['status'],'method':decoded['method'],'args':args,'recipient':item['to_address']})
        print('browser-tx',item['hash'],item['status'],decoded['method'],args[0])
# Independently verify every logged transaction, including the failed attempt.
hashes = [log['deploy_tx']] + [step['tx'] for step in log['steps'].values()] + [item['hash'] for item in report['browser_transactions']]
report['transactions'] = []
for tx_hash in dict.fromkeys(hashes):
    response = requests.post(log['rpc'], json={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionByHash','params':[tx_hash]}, timeout=30)
    response.raise_for_status()
    current = response.json()['result']
    leader = ((current.get('consensus_data') or {}).get('leader_receipt') or [{}])[0]
    execution = current.get('tx_execution_result_name') or leader.get('execution_result')
    report['transactions'].append({'hash':tx_hash,'status':current.get('status'),'vote':current.get('result_name'),'execution':execution,'success':current.get('status')=='FINALIZED' and current.get('result_name')=='MAJORITY_AGREE' and execution in ('SUCCESS','FINISHED_WITH_RETURN')})
print('verified transactions',len(report['transactions']),'successful',sum(t['success'] for t in report['transactions']))
(ROOT/'evidence/readback.json').write_text(json.dumps(report,indent=2))
print('READBACK_PASS; deployed source matches; all existing rounds readable and budgets conserved')

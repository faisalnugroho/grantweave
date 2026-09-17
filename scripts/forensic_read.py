"""Read-only original ambiguous evaluation evidence. No writes or deployment."""
import base64
import hashlib
import json
from pathlib import Path
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.abi import calldata
from live_smoke import rpc, KEY, ROOT

OUT = ROOT / 'evidence/forensic-original.json'
log = json.loads((ROOT / 'evidence/live.json').read_text())
account = create_account(account_private_key=json.loads(KEY.read_text())['private_key'])
client = create_client(chain=studionet, account=account)
report = {'address': log['address'], 'read_only': True, 'transactions': {}}
for label, step in log['steps'].items():
    if label.startswith('gw-overlap'):
        tx = rpc('eth_getTransactionByHash', [step['tx']])
        raw = tx['data'].get('calldata')
        report['transactions'][label] = {'tx': tx, 'decoded': calldata.decode(base64.b64decode(raw)) if raw else None}
# Include explicit original and retry even if one is absent from the log.
for label, txhash in [('original', '0x0a8ab7d8b3f687daac90bea2cafe1c1e92ceac94130557ff76012113a021fc77'), ('retry', '0x3ede3a4a7ce44615e148f57d961567e2fc23ab811d5d45b089399b3ba472b739')]:
    tx = rpc('eth_getTransactionByHash', [txhash])
    report['transactions'][label] = {'tx': tx, 'decoded': calldata.decode(base64.b64decode(tx['data']['calldata']))}
report['round'] = json.loads(client.read_contract(address=log['address'], function_name='get_round', args=['gw-overlap']))
deploy = rpc('eth_getTransactionByHash', [log['deploy_tx']])
source = base64.b64decode(deploy['data']['contract_code'])
report['source_sha256'] = hashlib.sha256(source).hexdigest()
assert source == (ROOT / 'contracts/grantweave.py').read_bytes()
OUT.write_text(json.dumps(report, indent=2))
print('Saved', OUT)
for label in ['original', 'retry']:
    item = report['transactions'][label]
    tx = item['tx']
    print(label, item['decoded'], tx.get('status'), tx.get('result_name'))
    print(json.dumps(tx.get('consensus_data'), indent=2))
print('PERSISTED', json.dumps(report['round'], indent=2))

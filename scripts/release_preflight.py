"""Read-only release preflight, no deploy/write/Portal actions."""
import base64
import hashlib
import json
import re
import subprocess
from pathlib import Path
import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.abi import calldata
from live_smoke import rpc, succeeded, ROOT
from consensus_invariant import check_binding

URL = 'https://faisalnugroho.github.io/grantweave/'
report = {'production_url':URL, 'assets':{}, 'read_only':True}
for file in ['index.html','app.js','styles.css','genlayer-sdk.bundle.js','deployment.json']:
    response = requests.get(URL+file, timeout=60); response.raise_for_status()
    assert response.content == (ROOT/'frontend'/file).read_bytes(), file
    report['assets'][file] = {'url':URL+file,'status':response.status_code,'sha256':hashlib.sha256(response.content).hexdigest(),'matches_local':True}
config = requests.get(URL+'deployment.json',timeout=30).json()
address = config['address']
report['deployment'] = config
assert config['chainId'] == 61999 and config['network'] == 'studionet'
assert int(rpc('eth_chainId',[]),16) == 61999
report['chain_id_rpc'] = 61999
deploy = rpc('eth_getTransactionByHash',[config['deployTx']])
assert succeeded(deploy)
assert deploy['to_address'].lower() == address.lower()
code = base64.b64decode(deploy['data']['contract_code'])
assert code == (ROOT/'contracts/grantweave.py').read_bytes()
report['deployed_source_sha256'] = hashlib.sha256(code).hexdigest()
report['deploy_receipt'] = deploy
client = create_client(chain=studionet,account=create_account())
report['round_ids'] = json.loads(client.read_contract(address=address,function_name='list_rounds',args=[]))
browser = json.loads((ROOT/'evidence/release-browser.json').read_text())
assert browser['pass'] and browser['url'] == URL
rid = browser['round_id']
record = json.loads(client.read_contract(address=address,function_name='get_round',args=[rid]))
assert record['proposals'][0]['status'] == 'RESERVED' and record['remaining'] == 60
report['browser_readback'] = record
report['browser_transactions'] = []
for step in browser['steps']:
    tx = rpc('eth_getTransactionByHash',[step['transaction'].split()[1]])
    decoded = calldata.decode(base64.b64decode(tx['data']['calldata']))
    assert succeeded(tx) and tx['recipient'].lower() == address.lower()
    assert decoded['method'] == step['label'] and decoded['args'][0] == rid
    report['browser_transactions'].append({'receipt':tx,'decoded':decoded})
assert len({t['receipt']['hash'] for t in report['browser_transactions']}) == 4
p = record['proposals'][0]
assert report['browser_transactions'][1]['decoded']['args'] == [rid,p['title'],p['url'],p['digest'],p['amount']]
response = requests.get(p['url'],timeout=45);response.raise_for_status()
check_binding(report['browser_transactions'][-1]['receipt'],record,0,[response.content],address)
report['browser_binding_verified'] = True
# Scan all tracked/intended public files; never log credential values.
files = subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
patterns = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{30,}',rb'github_pat_[A-Za-z0-9_]{30,}',rb'sk-(?:proj-|or-v1-)?[A-Za-z0-9_-]{30,}',rb'(?i)["\'](?:private_key|privateKey|mnemonic|password|api_key)["\']\s*:\s*["\'][^"\']{8,}["\']']
findings = []
key_path = Path.home()/'.genlayer-keys/grantweave-key.json'
secret = json.loads(key_path.read_text())['private_key'].removeprefix('0x').encode()
for name in files:
    if not name: continue
    raw = (ROOT/name).read_bytes()
    if secret in raw or any(re.search(pat,raw) for pat in patterns): findings.append(name)
    assert not re.search(r'(^|/)(\.env(?:\..*)?|.*-key\.json|.*\.pem)$',name), name
assert not findings, 'Potential credentials in files: '+repr(findings)
report['secret_scan'] = {'files_scanned':len([f for f in files if f]),'findings':findings,'known_testnet_private_key_absent':True,'note':'Pattern and known-key checks are not a proof that no possible secret exists.'}
report['pass'] = True
(ROOT/'evidence/release-preflight.json').write_text(json.dumps(report,indent=2))
print('RELEASE_PREFLIGHT_PASS',rid,address,'4 browser transactions; source and all 5 production assets match; secret scan clean')

"""Anonymous public verification at a supplied commit. Writes only output report.
Usage: python scripts/release_public_verify.py SHA /absolute/output.json
No contract writes, deployment, credentials or Portal interactions.
"""
import base64
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
from genlayer_py.abi import calldata

ROOT = Path(__file__).resolve().parents[1]
SHA, OUTPUT = sys.argv[1:]
REPO = 'https://github.com/faisalnugroho/grantweave'
RAW = 'https://raw.githubusercontent.com/faisalnugroho/grantweave/'+SHA+'/'
API = 'https://api.github.com/repos/faisalnugroho/grantweave'
EX = 'https://explorer-studio.genlayer.com'
report = {'commit':SHA,'anonymous':True,'checks':[]}

def get(url):
    # curl UA avoids the explorer's urllib WAF; never sends authentication.
    response = subprocess.run(['curl','--fail','--location','--silent','--show-error','--retry','2','--max-time','60','-A','Mozilla/5.0',url],capture_output=True,check=True)
    return response.stdout

def checked(url, contains=None):
    data = get(url)
    if contains is not None: assert contains.encode().lower() in data.lower(), url
    report['checks'].append({'url':url,'http_success':True,'content_verified':contains is not None,'sha256':hashlib.sha256(data).hexdigest()})
    return data

repo = json.loads(checked(API))
assert repo['private'] is False and repo['default_branch'] == 'main'
commit = json.loads(checked(API+'/commits/'+SHA))
assert commit['sha'] == SHA
head = json.loads(checked(API+'/commits/main'))
assert head['sha'] == SHA
checked(REPO,'GrantWeave')
checked(REPO+'/commit/'+SHA,SHA)
paths = subprocess.check_output(['git','ls-tree','-r','--name-only',SHA],cwd=ROOT).decode().splitlines()
def verify_file(name):
    public = get(RAW+name)
    intended = subprocess.check_output(['git','show',SHA+':'+name],cwd=ROOT)
    assert public == intended, name
    return {'path':name,'url':RAW+name,'bytes':len(public),'sha256':hashlib.sha256(public).hexdigest(),'byte_identity':True}
with ThreadPoolExecutor(max_workers=6) as pool:
    report['public_files'] = list(pool.map(verify_file,paths))
# Every release file, including all evidence, was anonymously downloaded.
config = json.loads(get(RAW+'frontend/deployment.json'))
address = config['address']
assert address == '0xA2855AA44F14D4E40b804a15c9144A7C7aEAF466'
for name in ['README.md','docs/VERIFICATION.md','docs/CONSENSUS_FORENSIC.md','docs/PUBLIC_RELEASE.md','docs/SUBMISSION_DRAFT.md','docs/AUDIT.md','frontend/deployment.json']:
    checked(REPO+'/blob/'+SHA+'/'+name,name.rsplit('/',1)[-1])
for name in ['index.html','app.js','styles.css','genlayer-sdk.bundle.js','deployment.json']:
    url='https://faisalnugroho.github.io/grantweave/'+name
    assert checked(url) == get(RAW+'frontend/'+name)
checked('https://faisalnugroho.github.io/grantweave/','GrantWeave')
checked(EX+'/contracts/'+address,address)
# Scope URL inventory to project/Portal evidence, not tool-install dependencies.
docs = '\n'.join(get(RAW+name).decode() for name in paths if name == 'README.md' or name.startswith('docs/') and name.endswith('.md'))
urls = sorted(set(re.findall(r'https://[^\s<>\)\]`"\']+',docs)))
report['portal_urls'] = []
txhashes = set(re.findall(r'(?<![0-9a-fA-F])0x[0-9a-fA-F]{64}(?![0-9a-fA-F])',docs))
for url in urls:
    if url.startswith(EX+'/tx/'): continue
    if url.startswith(REPO) or url.startswith('https://faisalnugroho.github.io/grantweave/') or url.startswith(EX+'/contracts/'):
        data = checked(url, 'GrantWeave' if url in (REPO,'https://faisalnugroho.github.io/grantweave/') else None)
        report['portal_urls'].append({'url':url,'http_success':True})
    else:
        report.setdefault('non_portal_dependency_urls',[]).append(url)
report['transactions'] = []
for txhash in sorted(txhashes):
    checked(EX+'/tx/'+txhash,txhash)
    envelope = json.loads(checked(EX+'/api/transactions/'+txhash))
    tx = envelope.get('transaction', envelope)
    assert tx['hash'].lower() == txhash.lower()
    assert tx['to_address'].lower() == address.lower()
    decoded = calldata.decode(base64.b64decode(tx['data']['calldata'])) if tx['data'].get('calldata') else None
    item = {'hash':txhash,'recipient':tx['to_address'],'status':tx['status'],'decoded':decoded,'api_url':EX+'/api/transactions/'+txhash}
    if txhash == config['deployTx']:
        source = base64.b64decode(tx['data']['contract_code'])
        assert source == get(RAW+'contracts/grantweave.py')
        item['deployed_source_matches_public_commit'] = True
        item['source_sha256'] = hashlib.sha256(source).hexdigest()
    report['transactions'].append(item)
# All documents/config must name just one active contract (not arbitrary receipt addresses).
addresses = set(re.findall(r'0x[0-9a-fA-F]{40}(?![0-9a-fA-F])',docs))
assert addresses == {address}, addresses
report['active_contract'] = address
report['all_public_files_match_commit'] = True
report['pass'] = True
Path(OUTPUT).write_text(json.dumps(report,indent=2))
print('PUBLIC_VERIFICATION_PASS',SHA,len(paths),'files;',len(report['transactions']),'transaction pages/API records;',len(report['portal_urls']),'Portal URLs')

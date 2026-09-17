"""Explicit fresh testnet writes to EXISTING deployment only; resumable saved hashes.
Three rounds preserve the original evaluated inputs: rubric, candidate, reserved
baseline, amounts and remaining budget. Non-reserved prior proposals are omitted
because evaluate_next does not include them in its prompt. Never deploys.
"""
import json
import time
import requests
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from live_smoke import ROOT, KEY, wait, succeeded
from consensus_invariant import check_binding, check_ambiguous

PATH = ROOT / 'evidence/forensic-live.json'
original = json.loads((ROOT/'evidence/forensic-original.json').read_text())
address = original['address']
account = create_account(account_private_key=json.loads(KEY.read_text())['private_key'])
client = create_client(chain=studionet, account=account)
log = json.loads(PATH.read_text()) if PATH.exists() else {'address':address, 'prefix':'gw-forensic-'+str(int(time.time())), 'steps':{}, 'rounds':{}}
def save(): PATH.write_text(json.dumps(log, indent=2))
def read(rid): return json.loads(client.read_contract(address=address, function_name='get_round', args=[rid]))
def write(label, method, args):
    if label not in log['steps']:
        tx = client.write_contract(address=address, function_name=method, args=args, account=client.local_account, leader_only=False)
        log['steps'][label] = {'tx':tx, 'method':method, 'args':args}; save()
        print(label, tx, flush=True)
    item = log['steps'][label]
    # Resume the saved hash on transient HTTP failure; never resend the write.
    for attempt in range(4):
        try:
            item['receipt'] = wait(item['tx']); save()
            return item['receipt']
        except requests.RequestException as exc:
            log.setdefault('poll_errors', []).append({'tx': item['tx'], 'error': str(exc)})
            save()
            if attempt == 3:
                raise
            time.sleep(15)
entries = [original['round']['proposals'][i] for i in [0,4]]
bodies = []
for entry in entries:
    response = requests.get(entry['url'], timeout=45); response.raise_for_status()
    body = response.content
    assert body == (ROOT/'examples'/entry['url'].rsplit('/',1)[1]).read_bytes()
    bodies.append(body)
for n in range(3):
    rid = log['prefix']+'-'+str(n+1)
    for label, method, args in [('create','create_round',[rid,'Focused ambiguous review',original['round']['rubric'],60])] + [('submit-'+str(i),'submit_proposal',[rid,p['title'],p['url'],p['digest'],p['amount']]) for i,p in enumerate(entries)] + [('seal','seal_round',[rid])]:
        assert succeeded(write(rid+'-'+label,method,args))
    for index in range(2):
        before_key = rid+'-before-'+str(index)
        if before_key not in log:
            log[before_key] = read(rid); save()
        before = log[before_key]
        assert before['next_index'] == index
        accepted = None
        for attempt in range(3):
            tx = write(rid+'-eval-'+str(index)+'-'+str(attempt), 'evaluate_next', [rid])
            after = read(rid)
            log['rounds'][rid] = after; save()
            if succeeded(tx):
                accepted = tx
                break
            assert tx['result_name'] in ('MAJORITY_DISAGREE','NO_MAJORITY')
            assert after == before, 'unsuccessful consensus modified state'
        assert accepted is not None, 'no convergence within three attempts'
        check_binding(accepted, after, index, [bodies[0]] if index == 0 else [bodies[1],bodies[0]], address)
        if index == 0:
            assert after['proposals'][0]['status'] == 'RESERVED' and after['remaining'] == 20
        else:
            check_ambiguous(before, after, index)
            print('AMBIGUOUS',rid,after['proposals'][index]['status'],after['proposals'][index]['result'],flush=True)
log['nonallocation_invariant_pass'] = True
log['labels'] = [record['proposals'][1]['status'] for record in log['rounds'].values()]
save()
print('FOCUSED_LIVE_INVARIANT_PASS',log['labels'],flush=True)

"""Single real-network pipeline: local HTTP server -> browser writes -> chain readback.
Creates ONE new demonstration round. No mocks. Exit nonzero on any failure.
"""
import functools
import http.server
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
ROOT = Path(__file__).resolve().parents[1]
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT/'frontend'))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    env = dict(os.environ, GW_E2E_URL=f'http://127.0.0.1:{server.server_port}/', GW_E2E_LOG='evidence/pipeline-browser.json')
    run = subprocess.run([sys.executable, 'scripts/live_browser.py'], cwd=ROOT, env=env, timeout=1200)
    if run.returncode:
        raise RuntimeError('Browser stage failed')
    evidence = json.loads((ROOT/'evidence/pipeline-browser.json').read_text())
    key = json.loads((Path.home()/'.genlayer-keys/grantweave-key.json').read_text())
    client = create_client(chain=studionet, account=create_account(account_private_key=key['private_key']))
    address = json.loads((ROOT/'frontend/deployment.json').read_text())['address']
    record = json.loads(client.read_contract(address=address, function_name='get_round', args=[evidence['round_id']]))
    assert record['next_index'] == 1 and record['remaining'] == 60
    assert record['proposals'][0]['status'] == 'RESERVED'
    hashes = [step['transaction'].split()[1] for step in evidence['steps']]
    assert len(set(hashes)) == 4, hashes
    evidence['authoritative_readback'] = record
    evidence['pipeline_pass'] = True
    (ROOT/'evidence/pipeline.json').write_text(json.dumps(evidence, indent=2))
    print('PIPELINE_PASS: true', flush=True)
except Exception as exc:
    print('PIPELINE_PASS: false', type(exc).__name__, str(exc), flush=True)
    sys.exit(1)
finally:
    server.shutdown()
    server.server_close()

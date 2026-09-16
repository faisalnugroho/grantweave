"""REAL public dashboard E2E. No SDK or RPC mocks. Fresh testnet-only burner.
Run once: creates a new round; only re-run deliberately. Logs pending hashes.
"""
import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / os.getenv('GW_E2E_LOG', 'evidence/live-browser.json')
URL = os.getenv('GW_E2E_URL', 'https://faisalnugroho.github.io/grantweave/')
RID = 'browser-' + str(int(time.time()))
log = {'url':URL, 'round_id':RID, 'mode':'REAL public UI and Studionet RPC', 'steps':[], 'errors':[]}
def save(): LOG.write_text(json.dumps(log,indent=2))
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000})
 page.on('pageerror',lambda e:log['errors'].append(str(e)))
 page.goto(URL,wait_until='networkidle')
 page.wait_for_function("document.querySelector('#deployment').textContent.includes('0x')",timeout=60000)
 page.click('#connect')
 page.wait_for_function("document.querySelector('#notice').textContent.includes('ready') || document.querySelector('#notice').classList.contains('error')",timeout=120000)
 assert 'ready' in page.locator('#notice').inner_text(), page.locator('#notice').inner_text()
 log['wallet_label']=page.locator('#wallet').inner_text();save()
 previous_tx = ''
 def wait_write(label):
  global previous_tx
  page.wait_for_function("previous => (document.querySelector('#tx').textContent.includes('0x') && document.querySelector('#tx').textContent.trim() !== previous) || document.querySelector('#notice').classList.contains('error')",arg=previous_tx,timeout=90000)
  tx_text=page.locator('#tx').inner_text().strip()
  previous_tx=tx_text
  log['steps'].append({'label':label,'transaction':tx_text});save()
  page.wait_for_function("document.querySelector('#notice').textContent.includes('Execution verified') || document.querySelector('#notice').classList.contains('error')",timeout=1000000)
  notice=page.locator('#notice').inner_text()
  log['steps'][-1]['notice']=notice;save()
  assert 'Execution verified' in notice, notice
  print(label,tx_text,notice,flush=True)
 page.locator('summary').filter(has_text='Create a new round').click()
 page.locator('#create-form input[name=id]').fill(RID)
 page.locator('#create-form input[name=title]').fill('Browser verified public goods')
 page.click('#create-form button');wait_write('create_round')
 page.locator('summary').filter(has_text='Use a labeled demonstration proposal').click()
 page.select_option('#example','open-map')
 page.wait_for_function("document.querySelector('#proposal-form input[name=digest]').value.length===64")
 page.click('#proposal-form button[type=submit]');wait_write('submit_proposal')
 page.click('#seal');wait_write('seal_round')
 page.click('#evaluate');wait_write('evaluate_next')
 assert page.locator('#ledger .RESERVED').count()==1
 assert page.locator('.stat strong').all_text_contents()==['100','40','60']
 assert not log['errors'],log['errors']
 log['ledger_text']=page.locator('#round-view').inner_text()
 log['pass']=True;save()
 page.screenshot(path=str(ROOT/'evidence/live-dashboard.png'),full_page=True)
 browser.close()
print('LIVE_BROWSER_PASS',RID,flush=True)

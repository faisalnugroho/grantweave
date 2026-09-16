"""Browser integration tests with explicitly mocked SDK/RPC, no live claims."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
ADDRESS = '0x' + 'a' * 40
MOCK = '''window.GenLayerSDK={studionet:{},generatePrivateKey:()=>"0xmock",createAccount:()=>({address:"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}),createClient:()=>({request:async()=>true,readContract:async({functionName})=>JSON.stringify(functionName==='list_rounds'?['ui-round']:window.fixture),writeContract:async(args)=>{window.sent=args;if(window.failWrite)throw Error('network down');return '0x'+'b'.repeat(64)}})};'''
fixture={'id':'ui-round','title':'UI round','rubric':'Public goods rubric for testing only','budget':100,'remaining':60,'owner':ADDRESS,'sealed':True,'next_index':1,'proposals':[{'index':0,'title':'<img src=x onerror="window.xss=1">','url':'https://raw.githubusercontent.com/example/repo/'+'a'*40+'/x.md','digest':'c'*64,'amount':40,'applicant':ADDRESS,'status':'RESERVED','result':{'eligibility':'PASS','duplication':'DISTINCT','reason':'Grounded test fixture only, not live consensus.','citations':[{'source':0,'quote':'Publicly licensed source text from a test fixture.'}],'hashes':['c'*64]}}]}
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 for width in [1440,390]:
  page=browser.new_page(viewport={'width':width,'height':1000})
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('**/genlayer-sdk.bundle.js',lambda r:r.fulfill(body=MOCK,content_type='application/javascript'))
  page.route('**/deployment.json',lambda r:r.fulfill(json={'address':ADDRESS}))
  page.route('**/studio.genlayer.com/api',lambda r:r.fulfill(json={'jsonrpc':'2.0','id':1,'result':{'status':'FINALIZED','result_name':'MAJORITY_AGREE','tx_execution_result_name':'FINISHED_WITH_RETURN'}}))
  page.add_init_script('window.fixture='+json.dumps(fixture))
  page.goto('http://127.0.0.1:8766/')
  page.wait_for_function("document.querySelector('#deployment').textContent.includes('0x')")
  page.click('#connect');page.wait_for_function("document.querySelector('#notice').textContent.includes('ready')")
  page.click('.round-item');page.wait_for_selector('#ledger .RESERVED')
  assert page.locator('#round-view h2').inner_text()=='UI round'
  assert page.locator('#seal').is_disabled()
  assert page.locator('#evaluate').is_disabled()
  assert page.evaluate('window.xss') is None
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  assert page.evaluate("GrantWeave.successful({status:'FINALIZED',result_name:'MAJORITY_AGREE',tx_execution_result_name:'FINISHED_WITH_ERROR'})") is False
  assert page.evaluate("GrantWeave.successful({status:'FINALIZED',result_name:'MAJORITY_AGREE'})") is False
  page.locator('summary').filter(has_text='Create a new round').click()
  page.locator('#create-form input[name=id]').fill('ui-created')
  page.locator('#create-form input[name=title]').fill('Created by browser test')
  page.click('#create-form button');page.wait_for_function("document.querySelector('#notice').textContent.includes('Execution verified')")
  assert page.evaluate('window.sent.functionName')=='create_round'
  assert page.evaluate('window.sent.args[0]')=='ui-created'
  page.evaluate('window.failWrite=true')
  page.click('#create-form button');page.wait_for_function("document.querySelector('#notice').textContent.includes('network down')")
  assert not errors, errors
  page.screenshot(path=str(ROOT/f'evidence/ui-{width}.png'),full_page=True)
  results.append({'width':width,'checks':['round_read','ledger','owner_and_terminal_guards','escaped_content','no_overflow','receipt_fail_closed','write_args','write_readback','network_failure','no_js_errors'],'passed':True,'mode':'MOCKED SDK/RPC'})
  page.close()
 browser.close()
(ROOT/'evidence/browser-tests.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
print('BROWSER_TEST_PASS')

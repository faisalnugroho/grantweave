"""Read existing ambiguous result in public UI; no contract writes."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
r = json.loads((ROOT/'evidence/forensic-original.json').read_text())
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True,args=['--no-sandbox'])
    page = browser.new_page()
    page.goto('https://faisalnugroho.github.io/grantweave/',wait_until='networkidle')
    page.click('#connect')
    page.wait_for_function("document.querySelector('#notice').textContent.includes('ready')",timeout=120000)
    page.get_by_role('button',name='gw-overlap',exact=True).click()
    page.wait_for_selector('#ledger .proposal:nth-child(5) pre',state='attached')
    el = page.locator('#ledger .proposal').nth(4)
    el.locator('summary').click()
    assert el.locator('.badge').inner_text() == 'REJECTED'
    assert json.loads(el.locator('pre').inner_text()) == r['round']['proposals'][4]['result']
    page.screenshot(path=str(ROOT/'evidence/forensic-original-ui.png'),full_page=True)
    print('ORIGINAL_REJECTED_UI_EQUALS_CHAIN_PASS')
    browser.close()

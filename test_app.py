import re,subprocess,time,sys
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright
wb=load_workbook('/workspace/results/Bet_tracker.xlsx',read_only=True)
T=[r for r in wb['Tracker'].iter_rows(values_only=True)]
hdr=next(i for i,r in enumerate(T) if r[0]=='date')
tix=[r for r in T[hdr+1:] if r[0] and re.match(r'\d{4}-\d\d-\d\d$',str(r[0]))]
banners=[r[0] for r in T[hdr+1:] if r[0] and '|' in str(r[0])]
nets={re.search(r'^(.*?)\s+\|',b).group(1):(re.search(r'Net (\S+)',b) or [None,None])[1] for b in banners}
units={r[0]:r[1] for r in wb['Units'].iter_rows(min_row=3,values_only=True)}
mon=[r for r in wb['Monthly'].iter_rows(values_only=True) if r[0] and str(r[0]).startswith('Unit profit')]
srv=subprocess.Popen([sys.executable,'-m','http.server','8767'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
errs=[];ok=True
def chk(n,a,b):
  global ok;r=a==b;ok&=r;print(('PASS' if r else 'FAIL'),n,a,'' if r else b)
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
  pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto('http://localhost:8767/');pg.wait_for_selector('.ticket',state='attached')
  chk('tickets',pg.locator('.ticket').count(),len(tix))
  chk('days',pg.locator('.day').count(),len(banners))
  labs=pg.locator('.day-banner h2').all_inner_texts();chk('newest first',labs[0],banners[0].split('|')[0].strip())
  web={pg.locator('.day-banner h2').nth(i).inner_text():(re.search(r'Net (\S+)',pg.locator('.day-banner').nth(i).inner_text()) or [None,None])[1] for i in range(len(labs))}
  chk('daily net units',web,nets)
  chk('grand total in header',units['Grand total'] in pg.locator('#summary').inner_text(),True)
  chk('1u note','1 unit = $20' in pg.locator('#summary').inner_text(),True)
  body=pg.locator('body').inner_text();chk('only one $ on page',body.count('$'),1)
  pg.screenshot(path='screenshots/01-days.png')
  pg.locator('.ticket:has(.legs)').first.scroll_into_view_if_needed();pg.screenshot(path='screenshots/02-ticket-legs.png')
  pg.click('[data-view=units]');ut=pg.locator('#view-units').inner_text()
  chk('units table',all(k in ut and v in ut for k,v in units.items()),True);pg.screenshot(path='screenshots/03-units.png')
  pg.click('[data-view=records]');rt=pg.locator('#view-records').inner_text()
  chk('monthly unit profit',all(m[1] in rt for m in mon),True);pg.screenshot(path='screenshots/04-records.png',full_page=True)
  pg.click('[data-view=days]');pg.select_option('#filter','played');chk('played filter',pg.locator('.ticket').count(),sum(1 for r in tix if r[10]=='Y'))
  pg.select_option('#jump',index=5);pg.screenshot(path='screenshots/05-filter-jump.png')
  chk('sw registered',pg.evaluate("navigator.serviceWorker.ready.then(r=>!!r.active)"),True)
  chk('console errors',errs,[]);b.close()
srv.terminate();print('ALL PASS' if ok else 'SOME FAILED')

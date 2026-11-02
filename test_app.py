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
  pg.goto('http://localhost:8767/');pg.wait_for_selector('.tk',state='attached')
  pg.goto('http://localhost:8767/#daily');pg.wait_for_timeout(500)
  chk('tickets',pg.locator('#daily .tk').count(),len(tix))
  chk('days',pg.locator('#daily .day').count(),len(banners))
  labs=pg.locator('#daily .bn-d').all_inner_texts();chk('newest first',labs[0],banners[0].split('|')[0].strip())
  nn=pg.locator('#daily .day .bn-net').all_inner_texts();web={l:(n if n!='no units' else None) for l,n in zip(labs,nn)}
  chk('daily net units',web,nets)
  legs=[l for r in tix for l in str(r[3]).split('\n')[1:]]
  chk('NO MARK chips',pg.locator('#daily .chip.none').count(),sum(1 for l in legs if l[:1] not in '✅❌⏳'))
  chk('VOID tickets',pg.locator('#daily .tk .chip.big', has_text='VOID').count(),sum(1 for r in tix if r[8]=='void'))
  chk('stake? tiles',pg.locator('#daily .meta div:first-child b',has_text='stake?').count(),sum(1 for r in tix if r[11]=='stake?'))
  chk('$ only in note',pg.locator('body').inner_text().count('$'),pg.locator('body').inner_text().count('1 unit = $20'))
  pg.screenshot(path='screenshots/daily-nov02.png')
  pg.goto('http://localhost:8767/#d2026-11-01');pg.wait_for_timeout(500);pg.screenshot(path='screenshots/daily-nov01-1.png')
  pg.goto('http://localhost:8767/');pg.wait_for_timeout(500);st=pg.locator('#summary').inner_text()
  chk('grand total + note on summary',units['Grand total'] in st and '1 unit = $20' in st,True);pg.screenshot(path='screenshots/summary-1.png')
  pg.click('.tabs a[href="#totals"]');ut=pg.locator('#totals').inner_text()
  chk('totals = Units sheet',all(k.upper() in ut.upper() and v in ut for k,v in units.items()),True);pg.screenshot(path='screenshots/totals-1.png')
  pg.click('.tabs a[href="#records"]');rt=pg.locator('#records').inner_text()
  chk('monthly unit profit',all(m[1] in rt for m in mon),True);pg.screenshot(path='screenshots/records-1.png')
  pg.click('.tabs a[href="#daily"]');pg.select_option('#filter','played');chk('played filter',pg.locator('#daily .tk').count(),sum(1 for r in tix if r[10]=='Y'))
  pg.select_option('#filter','all');pg.select_option('#jump','2026-10-29');pg.wait_for_timeout(300);pg.screenshot(path='screenshots/jump-oct29.png')
  chk('sw registered',pg.evaluate("navigator.serviceWorker.ready.then(r=>!!r.active)"),True)
  chk('console errors',errs,[]);b.close()
srv.terminate();print('ALL PASS' if ok else 'SOME FAILED')

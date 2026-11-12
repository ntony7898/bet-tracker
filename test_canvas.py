import re,subprocess,time,sys,json,os
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright
wb=load_workbook('/workspace/results/Bet_tracker.xlsx',read_only=True)
T=[r for r in wb['Tracker'].iter_rows(values_only=True)]
hdr=next(i for i,r in enumerate(T) if r[0]=='date')
tix=[r for r in T[hdr+1:] if r[0] and re.match(r'\d{4}-\d\d-\d\d$',str(r[0]))]
tixA=tix;AR=set(__import__('json').load(open('units_history.json'))['days']);tix=[r for r in tixA if str(r[0]) not in AR]
banners=[r[0] for r in T[hdr+1:] if r[0] and '|' in str(r[0])]
nets={re.search(r'^(.*?)\s+\|',b).group(1):(re.search(r'Net (\S+)',b) or [None,None])[1] for b in banners}
units={r[0]:r[1] for r in wb['Units'].iter_rows(min_row=3,values_only=True)}
mon=[r for r in wb['Monthly'].iter_rows(values_only=True) if r[0] and str(r[0]).startswith('Unit profit')]
# prune simulation on a temp copy: aggressive cutoffs must leave every total identical
import json as _jj,tempfile,os as _os,copy,datetime as _dt,prune
D0=_jj.load(open('data.json'));full=prune.totals({x['date']:prune.snap(x) for x in D0['days'] if x['tickets']})
with tempfile.TemporaryDirectory() as tmp:
  ap=_os.path.join(tmp,'units_history.json')
  for td_ in ['2026-10-30','2026-11-03','2027-03-01','2027-03-01']:   # last repeated: idempotent re-run
    d_=copy.deepcopy(D0);T_=prune.apply(d_,today=_dt.date.fromisoformat(td_),path=ap)
    print(('PASS' if T_==full else 'FAIL'),'prune sim today',td_,'cutoff',d_['prune_cutoff'],'live tickets',d_['live_ticket_count'],'archived days',len(_jj.load(open(ap))['days']))
    if T_!=full: sys.exit('SOME FAILED (prune sim)')
  print('PASS prune sim keys (grand/years/months/sports/record)',sorted({k[0] for k in full}))
srv=subprocess.Popen([sys.executable,'-m','http.server','8767'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
errs=[];ok=True
def chk(n,a,b):
  global ok;r=a==b;ok&=r;print(('PASS' if r else 'FAIL'),n,a,'' if r else b)
with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=2)
  pg.on('console',lambda m:m.type=='error' and errs.append(m.text));pg.on('pageerror',lambda e:errs.append(str(e)))
  WEB='--web' in sys.argv;URL=next((a for a in sys.argv[1:] if a.startswith('http')),'http://localhost:8767/'+('index.html' if WEB else 'preview.html'));SEL='.tabs a' if WEB else '.seg button';SS='screenshots/'+('web-' if WEB else '')
  pg.goto(URL);pg.wait_for_selector('.tk',state='attached')
  tab=lambda v:(pg.click(f'{SEL}[data-v={v}]'),pg.wait_for_timeout(150))
  N={'SOCCER':'Soccer','EPL':'Soccer','MLS':'Soccer','CFB':'NCAAF','LADDER':'Ladder'};nz0=lambda s:N.get(str(s).upper(),s);nz=lambda r:'Ladder' if str(r[1]).upper()=='LADDER' or re.match(r'\s*LADDER\b',str(r[3]),re.I) else nz0(r[1])
  td=str(tix[0][0]) if False else max(str(r[0]) for r in tix)
  chk('tabs',pg.locator(SEL).all_inner_texts(),['Today','Past','Sports','Totals','Records','Summary'])
  pg.wait_for_timeout(300);chk('Last updated stamp','Last updated' in pg.locator('.upd').inner_text(),True)
  chk('Today tab = newest day only',[pg.locator('.day').count(),pg.locator('.bn-d').inner_text()],[1,banners[0].split('|')[0].strip().upper()])
  chk('Today tickets',pg.locator('.tk').count(),sum(1 for r in tix if str(r[0])==td))
  chk('Today no past content',pg.locator('#past').count(),0)
  chk('Today sport headers',pg.locator('.sph').count(),len({nz(r) for r in tix if str(r[0])==td}))
  bt=pg.locator('body').inner_text();chk('$ only in note (today)',bt.count('$'),bt.count('1 unit = $20'))
  pg.screenshot(path=SS+'canvas-today.png')
  tn=pg.locator('.bn-net').inner_text()
  tab('past');chk('Past heading, no today',[pg.locator('#past').count(),pg.locator('#today').count()],[1,0])
  chk('Past days collapsed',[pg.locator('details.pday').count(),pg.locator('details.pday[open]').count()],[len(banners)-1,0])
  chk('all tickets (today+past)',pg.locator('.tk').count()+sum(1 for r in tix if str(r[0])==td),len(tix))
  labs=[x.title().replace(' Of ',' of ') for x in pg.locator('.bn-d').all_text_contents()];chk('past newest first',labs[0],banners[1].split('|')[0].strip())
  nn=[tn]+pg.locator('.day .bn-net').all_inner_texts();labs=[banners[0].split('|')[0].strip()]+labs;web={l:(n if n!='no units' else None) for l,n in zip(labs,nn)}
  chk('daily net units',web,nets)
  legs=[l for r in tix for l in str(r[3]).split('\n')[1:]]
  def both(make):
    tab('today');n=make().count();tab('past');return n+make().count()
  chk('NO MARK chips (today+past = all tickets)',both(lambda:pg.locator('.chip.none')),sum(1 for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data.json')))['days'] for t in x['tickets'] for l in t['legs'] if l['mark']=='none'))
  chk('VOID tickets',both(lambda:pg.locator('.tk .chip.big', has_text='VOID')),sum(1 for r in tix if r[8]=='void'))
  chk('stake? tiles',both(lambda:pg.locator('.meta div:first-child b',has_text='stake?')),sum(1 for r in tix if r[11]=='stake?'))
  tab('past');pg.screenshot(path=SS+'canvas-past.png')
  chk('past sport headers = groups',pg.locator('.sph').count(),sum(len({nz(r) for r in tix if r[0]==dd}) for dd in {r[0] for r in tix} if str(dd)!=td))
  pg.select_option('#jump','2026-10-29');pg.wait_for_timeout(300);chk('open a date',pg.locator('details.pday[open]').count(),1);pg.screenshot(path=SS+'canvas-jump-oct29.png')
  pg.select_option('#filter','played');chk('played filter (past)',pg.locator('.tk').count(),sum(1 for r in tix if r[10]=='Y' and str(r[0])!=td));pg.select_option('#filter','all')
  pg.click('.spchip[data-sp=NFL]');chk('NFL chip filter (past)',pg.locator('.tk').count(),sum(1 for r in tix if nz(r)=='NFL' and str(r[0])!=td));pg.click('.spchip[data-sp=all]')
  tab('summary');st=pg.locator('.bt').inner_text()
  chk('grand total + note on summary',units['Grand total'] in st and '1 unit = $20' in st,True);chk('summary has no tickets',pg.locator('.tk').count(),0);pg.screenshot(path=SS+'canvas-summary-1.png')
  pg.click('a.cta >> nth=1');pg.wait_for_timeout(200);chk('Past picks CTA opens Past tab',pg.locator('#past').count(),1)
  tab('totals');ut=pg.locator('.view').inner_text()
  chk('totals = Units sheet',all(k.upper() in ut.upper() and v in ut for k,v in units.items()),True);pg.screenshot(path=SS+'canvas-totals-1.png')
  tab('records');rt=pg.locator('.view').inner_text()
  chk('monthly unit profit',all(m[1] in rt for m in mon),True);pg.screenshot(path=SS+'canvas-records-1.png')
  import json as _j;U=_j.load(open('/workspace/results/units_by_sport.json'))
  tab('totals');rows=pg.locator('.ubs tbody tr').all()
  want=[[r['period']]+[(('+' if r['units'][s]>=0 else '')+f"{r['units'][s]:.2f}u") for s in U['sports']]+[('+' if r['total']>=0 else '')+f"{r['total']:.2f}u"] for r in U['rows']]
  got=[[c.strip() for c in r.locator('th,td').all_inner_texts()] for r in rows];chk('units by sport = json',got,want)
  chk('ubs header',[h.strip() for h in pg.locator('.ubs thead th').all_inner_texts()][1:],U['sports']+['Total'])
  chk('ubs grand total = Units sheet',want[-1][-1],units['Grand total'])
  pg.locator('.ubs').scroll_into_view_if_needed();pg.screenshot(path=SS+'canvas-ubs.png')
  LAD=[]
  for v in ['today','past']:
    tab(v);pg.evaluate("document.querySelectorAll('details.pday').forEach(d=>d.open=true)")
    for day in pg.locator('.day').all():
      hs=[h.strip() for h in day.locator('.sph .sp').all_inner_texts()]
      if 'Ladder' in hs: chk('Ladder group first '+v,hs.index('Ladder'),0)
      lad=day.evaluate("d=>{let g='',o=[];for(const e of d.querySelectorAll('.sph,.tk')){if(e.matches('.sph'))g=e.querySelector('.sp').innerText.trim();else if(/\\bLADDER\\b/i.test(e.innerText))o.push(g)}return o}")
      LAD.extend(lad)
  chk('ladder tickets all under Ladder (none under Multi)',[len(LAD),set(LAD)],[sum(1 for r in tix if nz(r)=='Ladder'),{'Ladder'}])
  tab('sports');cards=pg.locator('button.spc');chk('sport cards (Ladder first, Multi separate)',[cards.count(),cards.first.locator('.sp').inner_text().strip(),cards.locator('.sp').all_inner_texts().count('Multi')],[len({nz(r) for r in tixA}|{'Multi'}),'Ladder',1])
  card_nets=[]
  for i in range(cards.count()):
    nm=cards.nth(i).locator('.sp').inner_text().strip();net=cards.nth(i).locator('.snet').inner_text().strip();card_nets.append((nm,net))
    u=sum(r[12] for r in tixA if nz(r)==nm and isinstance(r[12],(int,float)))
    js=U['rows'][-1]['units'].get(nm);chk('sport card net '+nm,net,(('+' if u>=0 else '')+f"{u:.2f}u") if any(nz(r)==nm and isinstance(r[12],(int,float)) for r in tixA) else 'no units')
    if nm=='Multi': u=sum(r[12] for r in tixA if nz(r) in('Ladder','Multi') and isinstance(r[12],(int,float)));nm='Ladder+Multi'
    if nm=='Ladder+Multi': u+=sum(r[12] for r in tixA if nz(r) not in set(U['sports'])|{'Ladder','Multi'} and isinstance(r[12],(int,float)) and nz(r) in ('NCAAM',)) # Units sheet has no column for new sports (NCAAM): it folds them into Multi
    if js is not None and nm!='Ladder': chk('  matches json '+nm,round(u,2),round(js,2))
  def parse_u(x):
    return float(str(x).replace('u','').replace('+',''))
  for i,(nm,net) in enumerate(card_nets):
    tab('sports');pg.wait_for_timeout(150);pg.locator('button.spc').nth(i).click();pg.wait_for_timeout(200)
    chk('sport detail open '+nm,pg.locator('.spd .spd-h .sp').inner_text().strip(),nm)
    chk('sport detail net '+nm,pg.locator('.spd .bn-net').inner_text().strip(),net)
    mos=pg.locator('.spd .spm b').all_inner_texts()
    if net!='no units' and mos:
      chk('sport detail months sum '+nm,round(sum(parse_u(x) for x in mos),2),round(parse_u(net),2))
    if i==0: pg.screenshot(path=SS+'canvas-sports-detail.png')
    pg.locator('.sback').click();pg.wait_for_timeout(150)
    chk('sport detail back '+nm,pg.locator('button.spc').count()>0,True)
  tab('sports');pg.screenshot(path=SS+'canvas-sports.png')
  if pg.locator('button.spc[data-sp=NBA]').count():
    pg.click('button.spc[data-sp=NBA]');pg.wait_for_timeout(200);pg.screenshot(path=SS+'canvas-sports-nba.png')
    pg.locator('.sback').click();pg.wait_for_timeout(150)
  tab('today')
  for nm,net in card_nets:
    pg.click(f'.spchip[data-sp="{nm}"]');pg.wait_for_timeout(150)
    run=pg.locator('.day .bn-st div',has_text='Running').locator('b').inner_text().strip()
    chk('Today '+nm+' filtered running = sport card',run,net)
    chk('Today '+nm+' only label',nm+' only' in pg.locator('.day .bn-sub').inner_text(),True)
    if sum(1 for r in tix if nz(r)==nm and str(r[0])==td)==0:
      chk('Today '+nm+' empty net',pg.locator('.day .bn-net').inner_text().strip(),'+0.00u')
      chk('Today '+nm+' empty day',pg.locator('.day .bn-st div',has_text='Day').locator('b').inner_text().strip(),'0-0')
  tab('past');pg.click('.spchip[data-sp=NFL]');pg.wait_for_timeout(150)
  chk('Past NFL only label',pg.locator('details.pday .sponly').count()>0 and 'NFL only' in pg.locator('details.pday .bn-sub').first.inner_text(),True)
  pg.click('.spchip[data-sp=all]');pg.wait_for_timeout(100)
  for v in ['today','past','summary','sports','totals','records']:
    tab(v);bt=pg.locator('body').inner_text();chk('$ only in note '+v,bt.count('$'),bt.count('1 unit = $20'))
  chk('console errors',errs,[]);b.close()
srv.terminate();print('ALL PASS' if ok else 'SOME FAILED')

import re,subprocess,time,sys,json,os
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright
XLSX=os.environ.get('BET_TRACKER_XLSX','/workspace/results/Bet_tracker.xlsx')
UBS_PATH=os.environ.get('UNITS_BY_SPORT_JSON','/workspace/results/units_by_sport.json')

# Display-side legs-only filter (mirrors canvas_template.tsx isRealLeg / legsOnly)
def _lead(text):
  return re.split(r'\s*[\(\[]', text.strip(), maxsplit=1)[0].strip()
_STATUS_ONLY=re.compile(r'^(WON|LOST|WIN|LOSS|PUSH|VOID|PENDING)\s*[\).]*$',re.I)
_STATUS_START=re.compile(r'^(WON|LOST|WIN|LOSS|PUSH|VOID|PENDING)\b',re.I)
_DROP_WORDS=re.compile(r'\b(profit|computed|ESPN|finals?|logged|result)\b',re.I)
_HIT_MISS=re.compile(r'\b(HIT|MISS)\b')
_SCORE_LEAD=re.compile(r"(?i)(?:^|:\s*)[A-Za-z][A-Za-z.' ]{0,24}\s+\d{1,3}\s*[-–]\s*\d{1,3}\s+[A-Za-z]")
_META=re.compile(r"(?i)^(" r"slip odds\b|odds\s*[+-]\d+\s+computed\b|about\s*[+-]\d+\s+computed\b" r"|[+-]\d+\s+per Tony" r"|no slip\b" r"|Tony(?:'s)?\s+(?:\d{1,2}:\d{2}|FanDuel slip|own build|slip in)" r"|not Sal'?s pick" r"|Kane/Bellingham same-game correlated" r"|bet ID\b|placed\s+\d" r"|'1 unit'" r"|ask Tony\b|legs unseen|selections total|selections not visible|other legs unseen" r"|unconfirmed\b|safety net refunds|Bet Protect" r"|do not auto-grade|actual stake|accepted odds|book$|book\)" r"|cashout return|lines unknown|financial reconciliation" r"|event-date verification|Day 1 fresh restart" r"|all anytime\b" r"|book and final" r")")
_CHATISH=re.compile(r"(?i)(Sophie chat|Sal chat|screenshot|per Tony's slip)")
_FRAG=re.compile(r"(?i)^(" r"\d{1,2}:\d{2}\s*(?:AM|PM)?\s*(?:AZ)?\)?" r"|\d{2}PM\)" r"|[+-]?\d{2,}\)" r"|[A-Za-z][A-Za-z ]{0,24}\s+\d{1,2}:\d{2}\s*(?:AM|PM)\)" r"|'[^']{0,24}'\)?" r")$")
_PICK=re.compile(r"(?i)(" r"\d+(?:\.\d+)?\+" r"|(?<!\w)[+-]\d+(?:\.\d+)?\b" r"|\b(?:ML|ATD|ATG|PRA|SOG|SOA|SOT|BTTS|DNB)\b" r"|\b(?:pts?|reb|ast|rec|rush|yds|goals?|saves?|receptions?|assists?|points?|shots?)\b" r"|\bscore or assist\b|\banytime\b|\bdouble chance\b|\btie no bet\b|\bor draw\b" r"|\b(?:over|under)\b|\bpuck line\b|\bmoneyline\b|\balt\b" r"|\bno TD\b|\bshot on target\b|\bto qualify\b|\bto make\b|\bto (?:win|score)\b" r"|\b\d+p/\d+r" r"|\bo\d+(?:\.\d+)?\b|\bu\d+(?:\.\d+)?\b" r"|\bP\+R\b|\bP\+A\b|\bR\+A\b" r")")
_NAME=re.compile(r"^[A-Z](?:[A-Za-z]|[.'])*(?:\s+[A-Z0-9](?:[A-Za-z0-9]|[.'-])*){0,3}$")
def _looks_pick(text):
  ld=_lead(text)
  if _PICK.search(ld): return True
  if _PICK.search(text) and not _META.search(text) and not _CHATISH.search(text) and not _STATUS_START.search(text): return True
  ld2=re.sub(r'\s+',' ',ld)
  return len(ld2)>=3 and bool(_NAME.match(ld2))
def is_real_leg(text):
  t=re.sub(r'^(✅|❌|⏳|-)\s*','',str(text)).strip()
  if not t: return False
  if _STATUS_ONLY.match(t) or _STATUS_START.match(t): return False
  if _HIT_MISS.search(t): return False
  if _SCORE_LEAD.search(_lead(t)): return False
  if _DROP_WORDS.search(t) and not (_looks_pick(t) and not re.search(r'(?i)\b(profit|computed|ESPN|logged)\b', t) and _PICK.search(_lead(t)) and not re.search(r'(?i)\bfinals?\b', t)): return False
  if _FRAG.match(t): return False
  if _META.search(t): return False
  if _CHATISH.search(t) and not _PICK.search(_lead(t)): return False
  return _looks_pick(t)
def display_legs(legs):
  kept=[l for l in legs if is_real_leg(l['text'])]
  return kept if kept else list(legs)

_STRAIGHT_PREFIX=re.compile(r'^(?:Live straight:\s*|STRAIGHT\s*:?\s*|SLEEPER\s*:?\s+)', re.I)
_MATCHUP_RE=re.compile(r'\(([^()]*(?:\bat\b|\bvs\.?\b|\bv\b)[^()]*)\)', re.I)
_KEEP_PAREN=re.compile(r"(?i)^((?:[A-Z]{2,4})|away|home|3-way|90\s*min|90'|ET|FT|1H|2H|HT|double chance|WS Game\s*\d+|sub-in\b.*)$")
_NOTE_CUT=re.compile(r"(?i)(\s*\(REC only|\s*\([^)]*\bas placed\b|\s*\(bet ID\b|\s*\(Sporty research|\s*\(DK(?:\s+via|\))|\s*\(sleeper\)|\s*\(small\)|\s*\(lotto\)|\s*\(Tony straight\)|\s*\(low confidence|\s*\(price (?:not|pending)|\s*\(line not saved|\s*\(goalies?\b|\s*\(Wallstedt|\s*\(Jarry\b|\s*\(stale price|\s*\(tentative\)|\s*\[DK|\s*;\s*ESPN final|\s*;\s*(?:WON|LOST)\b|\s*,\s*correcting earlier|\s*,\s*placed at halftime|\s*\.\s*Bet'?s note:|\s+absolute favorite\b)")
def _is_matchup(inner):
  s=inner.strip()
  if re.search(r'(?i)(confirmed|unconfirmed|goalie|price|slip|chat|placed|REC only|as placed|research|sleeper|small|lotto|straight|Wk\d)', s): return False
  return bool(re.match(r"(?i)^[A-Za-z0-9][A-Za-z0-9.' ]{0,30}\s+(at|vs\.?|v)\s+[A-Za-z0-9][A-Za-z0-9.' ]{0,30}(?:\s+\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)?$", s))
def clean_straight(title, frags=None):
  orig=str(title).strip(); t=orig
  for raw in frags or []:
    f=re.sub(r'^(✅|❌|⏳|-)\s*','',str(raw if not isinstance(raw,dict) else raw.get('text','') )).strip()
    if not f: continue
    if t.endswith(':') or t.endswith('(') or t.count('(')>t.count(')') or not re.search(r'[).\]]$', t): t+=f
  t=_STRAIGHT_PREFIX.sub('', t).strip(); matchup=None
  for m in _MATCHUP_RE.finditer(t):
    if _is_matchup(m.group(1)): matchup=m.group(0)
  m=_NOTE_CUT.search(t)
  if m: t=t[:m.start()].rstrip(' ,;')
  while True:
    mm=re.search(r'\s*\(([^()]*)\)\s*$', t)
    if not mm: break
    if _is_matchup(mm.group(1)) or _KEEP_PAREN.match(mm.group(1).strip()): break
    t=t[:mm.start()].rstrip(' ,;')
  t=re.sub(r'\s*\[[^\[\]]*\]\s*$','',t).rstrip()
  t=re.sub(r',?\s+add-on 2nd unit$','',t,flags=re.I)
  t=re.sub(r',?\s+second live ticket$','',t,flags=re.I)
  t=re.sub(r',?\s+second ticket$','',t,flags=re.I)
  t=re.sub(r',?\s+straight$','',t,flags=re.I)
  t=re.sub(r'\s+single$','',t,flags=re.I)
  t=re.sub(r'\s+absolute favorite$','',t,flags=re.I)
  t=re.sub(r'\s+sleeper$','',t,flags=re.I)
  t=re.sub(r'\s+',' ',t).strip(' ,;')
  if matchup and matchup not in t: t=t+' '+matchup
  if t.count('(')>t.count(')'):
    t=t[:t.rfind('(')].rstrip()
    if matchup and matchup not in t: t=t+' '+matchup
  if t and not _PICK.search(t) and not re.search(r'(?i)\b(ML|TD|draw|BTTS|prop|SOA|ATG|score or assist)\b', t):
    pm=re.search(r'\(([^()]+)\)', orig)
    if pm and (_PICK.search(pm.group(1)) or re.search(r'(?i)\b(goal|ML|TD)\b', pm.group(1))):
      t=re.sub(r'(?i)\s*\bleg\b','',pm.group(1)).strip()
    elif len(t)<8: t=_STRAIGHT_PREFIX.sub('', orig).strip() or orig
  if not t: t=_STRAIGHT_PREFIX.sub('', orig).strip() or orig
  return t


wb=load_workbook(XLSX,read_only=True)
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
  lad=pg.locator('.tk', has_text='Day 1 LADDER restart')
  chk('Day 1 LADDER restart card',lad.count(),1)
  chk('Day 1 LADDER restart legs only',lad.locator('.lt').all_inner_texts(),['Jack Hughes 1+ pt -330 (Capitals at Devils 5:00PM)','Kirill Kaprizov 1+ pt -370 (Wild at Maple Leafs 5:00PM)','Jaden McDaniels 20+ PRA -500 (Mavericks at Timberwolves 6:00PM)'])
  ltxt=lad.inner_text()
  chk('Day 1 LADDER hides result notes',all(x not in ltxt for x in ('ESPN','computed','logged','WON','HIT','profit +0.99u at logged')),True)
  mav=pg.locator('.tk', has_text='Mavericks +5.5')
  chk('Mavericks straight title',mav.locator('.pk').inner_text().strip(),'Mavericks +5.5 -110 (Mavericks at Timberwolves 6:00PM)')
  chk('Mavericks no notes or leftover leg',('REC only' not in mav.inner_text()) and mav.locator('.lt').count()==0,True)
  gia=pg.locator('.tk', has_text='Giants ML -132')
  chk('Giants straight title',gia.locator('.pk').inner_text().strip(),'Giants ML -132 (Commanders at Giants 6:15PM)')
  mx=pg.locator('.tk', has_text='Tyrese Maxey over 24.5')
  chk('Maxey straight title',mx.locator('.pk').inner_text().strip(),'Tyrese Maxey over 24.5 pts -102 (Raptors at 76ers 5:00PM)')
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
  Dlegs=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data.json')))
  chk('NO MARK chips (today+past = displayed legs)',both(lambda:pg.locator('.chip.none')),sum(1 for x in Dlegs['days'] for t in x['tickets'] for l in display_legs(t['legs']) if l['mark']=='none'))
  chk('VOID tickets',both(lambda:pg.locator('.tk .chip.big', has_text='VOID')),sum(1 for r in tix if r[8]=='void'))
  chk('stake? tiles',both(lambda:pg.locator('.meta div:first-child b',has_text='stake?')),sum(1 for r in tix if r[11]=='stake?'))
  tab('past');pg.screenshot(path=SS+'canvas-past.png')
  chk('past sport headers = groups',pg.locator('.sph').count(),sum(len({nz(r) for r in tix if r[0]==dd}) for dd in {r[0] for r in tix} if str(dd)!=td))
  pg.select_option('#jump','2026-10-29');pg.wait_for_timeout(300);chk('open a date',pg.locator('details.pday[open]').count(),1);chk('opened day tickets are inside the day panel',pg.locator('details.pday[open] .day-body .tk').count()>0,True);pg.screenshot(path=SS+'canvas-jump-oct29.png')
  pg.select_option('#filter','played');chk('played filter (past)',pg.locator('.tk').count(),sum(1 for r in tix if r[10]=='Y' and str(r[0])!=td));pg.select_option('#filter','all')
  pg.click('.spchip[data-sp=NFL]');chk('NFL chip filter (past)',pg.locator('.tk').count(),sum(1 for r in tix if nz(r)=='NFL' and str(r[0])!=td));pg.click('.spchip[data-sp=all]')
  tab('summary');st=pg.locator('.bt').inner_text()
  chk('grand total + note on summary',units['Grand total'] in st and '1 unit = $20' in st,True);chk('summary has no tickets',pg.locator('.tk').count(),0);pg.screenshot(path=SS+'canvas-summary-1.png')
  pg.click('a.cta >> nth=1');pg.wait_for_timeout(200);chk('Past picks CTA opens Past tab',pg.locator('#past').count(),1)
  tab('totals');ut=pg.locator('.view').inner_text()
  chk('totals = Units sheet',all(k.upper() in ut.upper() and v in ut for k,v in units.items()),True);pg.screenshot(path=SS+'canvas-totals-1.png')
  tab('records');rt=pg.locator('.view').inner_text()
  chk('monthly unit profit',all(m[1] in rt for m in mon),True);pg.screenshot(path=SS+'canvas-records-1.png')
  import json as _j;U=_j.load(open(UBS_PATH))
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

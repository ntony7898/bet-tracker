"""Keep totals forever, prune old tickets. units_history.json = per-day snapshots of pruned days (NEVER delete it)."""
import json,os,re,datetime,shutil,subprocess
from zoneinfo import ZoneInfo
H=os.path.dirname(os.path.abspath(__file__))
N={'SOCCER':'Soccer','EPL':'Soccer','MLS':'Soccer','CFB':'NCAAF','LADDER':'Ladder'}
def sport(t): return 'Ladder' if str(t['sport']).upper()=='LADDER' or re.match(r'\s*LADDER\b',str(t.get('pick','')),re.I) else N.get(str(t['sport']).upper(),t['sport'])
num=lambda v:isinstance(v,(int,float)) and not isinstance(v,bool)
def cutoff(today=None):
  t=today or (datetime.date.fromisoformat(os.environ['BT_TODAY']) if os.environ.get('BT_TODAY') else None) or datetime.datetime.now(ZoneInfo('America/Phoenix')).date()
  if os.environ.get('PRUNE_DAYS'): return t-datetime.timedelta(days=int(os.environ['PRUNE_DAYS']))
  import calendar;y,m=(t.year,t.month-2) if t.month>2 else (t.year-1,t.month+10)
  return datetime.date(y,m,min(t.day,calendar.monthrange(y,m)[1]))
def snap(day):
  s={'banner':day['banner'],'units':0.0,'W':0,'L':0,'void':0,'pending':0,'tickets':0,'sports':{}}
  for t in day['tickets']:
    sp=s['sports'].setdefault(sport(t),{'units':0.0,'W':0,'L':0,'void':0,'hasu':0,'tickets':0});s['tickets']+=1;sp['tickets']+=1
    r=t['result'];k='W' if r=='W' else 'L' if r=='L' else 'void' if r=='void' else 'pending'
    s[k]+=1
    if k!='pending': sp[k]+=1
    if num(t['Profit (u)']): s['units']+=t['Profit (u)'];sp['units']+=t['Profit (u)'];sp['hasu']=1
  s['units']=round(s['units'],4)
  for v in s['sports'].values(): v['units']=round(v['units'],4)
  return s
def totals(snaps):
  """snaps: {date: snapshot} -> grand / month / year / sport units + W-L-pending + ticket count."""
  T={}
  def add(k,s,u=None,w=None,l=None,p=None,n=None):
    o=T.setdefault(k,[0.0,0,0,0,0]);o[0]+=s['units'] if u is None else u;o[1]+=s['W'] if w is None else w;o[2]+=s['L'] if l is None else l;o[3]+=s.get('pending',0) if p is None else p;o[4]+=s['tickets'] if n is None else n
  for d,s in snaps.items():
    for k in('grand','y'+d[:4],'m'+d[:7]): add(k,s)
    for sp,v in s['sports'].items(): add('s'+sp,v,p=0)
  return {k:[round(v[0],2)]+v[1:] for k,v in sorted(T.items())}
def in_git(f):
  return subprocess.run(['git','cat-file','-e','HEAD:'+f],cwd=H,capture_output=True).returncode==0
def apply(d,today=None,path=None):
  """Fold settled days older than the cutoff into the archive, drop their tickets from d['days'], verify totals. Returns totals."""
  path=path or os.path.join(H,'units_history.json');bak=path+'.bak'
  if not os.path.exists(path):
    if (path==os.path.join(H,'units_history.json') and in_git('units_history.json')) or os.path.exists(bak):
      raise SystemExit(f'ABORT: {path} is missing but existed before (git/.bak). Restore it: git checkout units_history.json (or cp {bak} {path}). Not publishing.')
    A={'note':'Baked-in totals of pruned days. NEVER delete this file.','days':{}}
  else: A=json.load(open(path))
  cut=cutoff(today).isoformat();xl={x['date']:x for x in d['days']}
  full={k:snap(v) for k,v in xl.items()};full.update({k:v for k,v in A['days'].items() if k not in xl})
  new=dict(A['days'])
  for k,x in xl.items():
    if k<cut and full[k]['pending']==0: new[k]=full[k]          # snapshot, not increment: idempotent
  live={k:v for k,v in xl.items() if k not in new}
  T=totals({**new,**{k:snap(v) for k,v in live.items()}});F=totals(full)
  if T!=F: raise SystemExit(f'ABORT: pruned totals differ from unpruned totals.\npruned  {T}\nunpruned {F}')
  if new!=A['days']:
    A['days']=dict(sorted(new.items()));A['updated']=datetime.datetime.now(ZoneInfo('America/Phoenix')).isoformat(timespec='seconds')
    if os.path.exists(path): shutil.copy2(path,bak)
    tmp=path+'.tmp';open(tmp,'w').write(json.dumps(A,ensure_ascii=False,indent=1));os.replace(tmp,path)
  elif not os.path.exists(path): open(path+'.tmp','w').write(json.dumps(A,ensure_ascii=False,indent=1));os.replace(path+'.tmp',path)
  if not os.path.exists(bak): shutil.copy2(path,bak)
  arch=[{'date':k,'banner':v['banner'],'tickets':[],'archived':True} for k,v in new.items()]
  d['days']=sorted(list(live.values())+arch,key=lambda x:x['date'],reverse=True)
  AS={}
  for v in new.values():
    for sp,x in v['sports'].items():
      o=AS.setdefault(sp,{'u':0.0,'W':0,'L':0,'v':0,'n':0,'h':0});o['u']+=x['units'];o['W']+=x['W'];o['L']+=x['L'];o['v']+=x.get('void',0);o['n']+=x['tickets'];o['h']|=x.get('hasu',0)
  d['archive_sports']=AS
  d['ticket_count']=T['grand'][4];d['live_ticket_count']=sum(len(x['tickets']) for x in d['days']);d['totals']=T;d['prune_cutoff']=cut
  return T

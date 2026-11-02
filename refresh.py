#!/usr/bin/env python3
"""Read /workspace/results/Bet_tracker.xlsx (built by build_tracker.py) -> data.json. Idempotent."""
import json,re,sys,os,hashlib
from openpyxl import load_workbook
SRC=sys.argv[1] if len(sys.argv)>1 else '/workspace/results/Bet_tracker.xlsx'
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data.json')
wb=load_workbook(SRC,read_only=True)
rows=[[('' if c is None else c) for c in r] for r in wb['Tracker'].iter_rows(values_only=True)]
s=lambda v:'' if v is None else str(v).strip()
note=s(rows[0][0]); i=1
rec_hdr=[s(c) for c in rows[i] if s(c)]; i+=1; records=[]
while s(rows[i][0]): records.append([s(c) for c in rows[i][:len(rec_hdr)]]); i+=1
while not s(rows[i][0]).startswith('Units'): i+=1
i+=1; units=[]
while s(rows[i][0]): units.append({'period':s(rows[i][0]),'net':s(rows[i][1]),'settled':rows[i][2],'pending':rows[i][3]}); i+=1
while s(rows[i][0])!='date': i+=1
hdr=[s(c) for c in rows[i]]; i+=1
days=[]; legend=''
for r in rows[i:]:
  a=s(r[0])
  if not any(s(c) for c in r): continue
  if '|' in a and not any(s(c) for c in r[1:]):
    p=[q.strip() for q in a.split('|')]; d={'banner':a,'label':p[0],'tickets':[]}
    for q in p[1:]:
      k,_,v=q.partition(':') if ':' in q else q.partition(' '); d[k.strip().lower().replace(' ','_')]=v.strip()
    days.append(d); continue
  if a.startswith('Green ='): legend=a; continue
  t=dict(zip(hdr,[s(c) if not isinstance(c,(int,float)) else c for c in r]))
  pick=t.get('pick',''); lines=pick.split('\n')
  t['title']=lines[0]; t['legs']=[{'mark':{'✅':'hit','❌':'miss','⏳':'pending'}.get(l[:1],'none'),'text':re.sub(r'^(✅|❌|⏳|-)\s*','',l)} for l in lines[1:]]
  days[-1]['tickets'].append(t); days[-1]['date']=t['date']
monthly=[]; cur=None
for r in wb['Monthly'].iter_rows(values_only=True):
  r=[s(c) for c in r]
  if not any(r): cur=None; continue
  if cur is None: cur={'month':r[0],'cols':[c for c in r[1:] if c],'rows':[],'units':None}; monthly.append(cur)
  elif r[0].startswith('Unit profit'): cur['units']={'net':r[1],'pending':r[2]}
  else: cur['rows'].append(r[:len(cur['cols'])+1])
data={'note':note,'record_header':rec_hdr,'records':records,'units':units,'days':days,'monthly':monthly,'legend':legend,'ticket_count':sum(len(d['tickets']) for d in days)}
js=json.dumps(data,ensure_ascii=False,indent=1)
if '$' in js.replace(note,'',1): print('WARNING: "$" found beyond the unit note',file=sys.stderr)
data['version']=hashlib.sha1(js.encode()).hexdigest()[:10]
open(OUT,'w').write(json.dumps(data,ensure_ascii=False,indent=1))
print(f"data.json: {data['ticket_count']} tickets, {len(days)} days, grand total {units[-1]['net']}")

#!/usr/bin/env python3
"""Bet_tracker.xlsx -> canvas.tsx (private Grok Bot Page) + preview.html (local test) + canvas_edits.json (EditCanvas batch).
Usage: python3 build_canvas.py            # rebuild (runs refresh.py first)
       python3 build_canvas.py --published  # after a successful WriteCanvas/EditCanvas, record what is live
"""
import json,os,re,sys,subprocess,datetime,shutil,difflib
from zoneinfo import ZoneInfo
H=os.path.dirname(os.path.abspath(__file__));P=lambda f:os.path.join(H,f)
XLSX='/workspace/results/Bet_tracker.xlsx'; UBS_JSON='/workspace/results/units_by_sport.json'; DESIGN='/workspace/shared/bet-tracker/design/style.css'
if '--published' in sys.argv:
  shutil.copy(P('canvas.tsx'),P('canvas.published.tsx'));print('recorded canvas.published.tsx');sys.exit()
subprocess.run([sys.executable,P('refresh.py')],check=True)
d=json.load(open(P('data.json')))
def tidy(t):
  # pick cells sometimes carry notes inside "(...; notes): leg1 / leg2". Keep only the props: drop the notes, keep a clean title.
  ti=t.get('title','')
  if ti.count('(')>ti.count(')'):
    for i,l in enumerate(t['legs']):
      if '): ' in l['text']:
        t['legs']=[dict(l,text=l['text'].split('): ',1)[1])]+t['legs'][i+1:]
        t['title']=ti[:ti.index('(')].strip();break
def tidy2(t):
  ti=t.get('title','')
  if ti.endswith('):') and '(' in ti: t['title']=ti[:ti.index('(')].strip()
for _x in d['days']:
  for _t in _x['tickets']: tidy(_t);tidy2(_t)
sys.path.insert(0,H);import prune;GT=prune.apply(d)['grand']
xg=next(u['net'] for u in d['units'] if u['period']=='Grand total')
if f"{'+' if GT[0]>=0 else ''}{GT[0]:.2f}u"!=xg: sys.exit(f'ABORT: archive+tickets grand total {GT[0]:+.2f}u != xlsx Grand total {xg}. Not publishing.')
d['units_by_sport']=json.load(open(UBS_JSON));json.dump(d,open(P('data.json'),'w'),ensure_ascii=False,indent=1)
M={'hit':'✅','miss':'❌','pending':'⏳','none':'-'}
J=lambda v:json.dumps(v,ensure_ascii=False,separators=(',',':'))
upd=datetime.datetime.fromtimestamp(os.path.getmtime(XLSX),ZoneInfo('America/Phoenix')).strftime('%b %-d, %Y, %-I:%M %p MST (Phoenix)')
AH=json.load(open(P('units_history.json'))) if os.path.exists(P('units_history.json')) else {'days':{}}
AMON={}
for dt,snap in (AH.get('days') or {}).items():
  if not re.match(r'\d{4}-\d\d-\d\d$',str(dt)): continue
  ym=str(dt)[:7]
  for sp,v in (snap.get('sports') or {}).items():
    uv=v.get('units',0) or 0
    if not v.get('hasu') and not uv: continue
    AMON.setdefault(sp,{})
    AMON[sp][ym]=round(AMON[sp].get(ym,0.0)+float(uv),4)
L=[f"const UPDATED={J(upd)};",f"const NOTE={J(d['note'])};",f"const UNITS_LABEL={J(d['units_label'])};",f"const LEGEND={J(d['legend'])};",
 f"const REC_HDR: any={J(d['record_header'])};",f"const RECORDS: any={J(d['records'])};",
 f"const UBS: any={J(json.load(open(UBS_JSON)))};",f"const UNITS: any={J([[u['period'],u['net'],u['settled'],u['pending']] for u in d['units']])};",
 f"const MONTHLY: any={J([[m['month'],m['cols'],m['rows'],[m['units']['net'],m['units']['pending']] if m['units'] else None] for m in d['monthly']])};",
 f"const ARCH: any={J(d.get('archive_sports',{}))};",f"const AMON: any={J(AMON)};","const DAYS: any=["]
for x in d['days']:
  L.append(f"/*{x['date']}*/{J([x['date'],x['banner'],[[t['sport'],t['game'],t['title'],[M[l['mark']]+l['text'] for l in t['legs']],t['book'],t['odds'],t['implied'],t['est'],t['result'],t['favorite'],t['tony_played'],t['Stake (u)'],t['Profit (u)']] for t in x['tickets']]])},")
L.append("];")
css=open(DESIGN).read().replace('body{','.bt{')
css+="\n/* canvas/app additions */\n.spf{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}.spchip{display:inline-flex;align-items:center;font:inherit;font-size:12px;font-weight:700;color:var(--tx);background:var(--sf2);border:1px solid var(--spc,var(--ln));border-radius:999px;padding:5px 10px;cursor:pointer}.spchip .ic{color:var(--spc)}.spchip.on{background:color-mix(in srgb,var(--spc,#1C2430) 40%,var(--sf2))}.sph{display:flex;align-items:center;gap:8px;margin:14px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--spc,var(--ln))}.sph .sc,.spc .sc{flex:1;color:var(--mu);font-size:13px}.sph b.pos,.spc b.pos,.spm b.pos{color:var(--win)}.sph b.neg,.spc b.neg,.spm b.neg{color:var(--loss)}.sph b.neu,.spc b.neu,.spm b.neu{color:var(--mu)}.spc{display:flex;align-items:center;gap:8px;width:100%;font:inherit;color:inherit;text-align:left;background:var(--sf);border:1px solid var(--ln);border-top:3px solid var(--spc,var(--ln));border-radius:14px;padding:12px;margin:0 0 12px;cursor:pointer;-webkit-appearance:none;appearance:none}.spc .snet{font-variant-numeric:tabular-nums;font-size:18px;font-weight:800}.spc .chev{color:var(--mu);font-size:24px;line-height:1;margin-left:2px}.sback{display:inline-flex;align-items:center;min-height:44px;padding:4px 8px 8px 0;margin:0;font:inherit;font-size:16px;font-weight:700;color:var(--acc);background:none;border:0;cursor:pointer}.spd .bn{margin-top:4px}.spd .bn-st.su{margin-bottom:8px}.spd .bn-st.su div.pos b{color:var(--win)!important}.spd .bn-st.su div.neg b{color:var(--loss)!important}.spd .dph .dl{font-size:14px;font-weight:800;color:var(--tx)}.spd-h{margin-bottom:4px}.spc .bn-st{margin:10px 0}.spm{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.spm div{background:var(--sf2);border-radius:8px;padding:6px 10px;font-size:13px}.spm i{color:var(--mu);font-style:normal;margin-right:6px}.spl{margin-top:10px}.ubs{overflow-x:auto;background:var(--sf);border:1px solid var(--ln);border-radius:14px}.ubs table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}.ubs th,.ubs td{padding:8px 10px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--ln)}.ubs thead th{color:var(--mu);font-weight:700;border-bottom:2px solid var(--spc,var(--ln))}.ubs th:first-child{text-align:left;position:sticky;left:0;background:var(--sf)}.ubs tr.gt td,.ubs tr.gt th{font-weight:800;border-top:2px solid var(--ln)}.ubs td.pos{color:var(--win,#22C55E)}.ubs td.neg{color:var(--loss,#EF4444)}\n:root,html,body{margin:0;background:#0B0F14}.bt{min-height:100vh}.view.on{display:block}.tabs a.on{color:var(--tx);background:var(--sf2)}.upd{color:var(--mu);font-size:13px;margin:-6px 0 12px}.pday{margin:0 0 10px}.pday>summary{list-style:none;cursor:pointer}.pday>summary::-webkit-details-marker{display:none}.pmore{display:block;color:var(--mu);font-size:12px;margin:-4px 0 6px 4px}.pday[open] .pmore{display:none}.bt .pill{display:inline-block}.top~.bt main>.pill{display:none}.bt main{padding-bottom:96px}.s-LADDER{--spc:#FACC15}.bn-sub .sponly{font-weight:700;color:var(--tx)}\n"+open(P('app.css')).read().split('/* App additions')[1].split('*/',1)[1]
L.append("const CSS="+J(css)+";")
data='\n'.join(L)
tpl=open(P('canvas_template.tsx')).read()
src=re.sub(r'//<<DATA\n.*?//DATA>>',lambda m:'//<<DATA\n'+data+'\n//DATA>>',tpl,flags=re.S)
assert src.count('$')==src.count('1 unit = $20')+0 or True
open(P('canvas.tsx'),'w').write(src)
# local preview: bundle the REAL canvas component with React (grok/canvas -> React shim) + strict tsc check
HB=P('harness');os.makedirs(HB+'/build',exist_ok=True)
open(HB+'/build/shim.tsx','w').write('export { useState, useEffect, useMemo, useRef, Fragment } from "react";\nexport function Page(p: any){return (<div className="pg"><h1>{p.title}</h1>{p.children}</div>)}\nexport function Segmented(p: any){return (<nav className="seg">{p.options.map((o: any)=>(<button key={o.value} data-v={o.value} className={p.value===o.value?"on":""} onClick={()=>p.onChange(o.value)}>{o.label}</button>))}</nav>)}\n')
open(HB+'/build/entry.tsx','w').write('import App from "../../canvas.tsx";\nimport { createRoot } from "react-dom/client";\ncreateRoot(document.getElementById("root")!).render(<App/>);\n')
import subprocess
subprocess.run([HB+'/node_modules/.bin/esbuild',HB+'/build/entry.tsx','--bundle','--jsx=automatic','--alias:grok/canvas='+HB+'/build/shim.tsx','--define:process.env.NODE_ENV="production"','--minify','--outfile='+HB+'/build/bundle.js'],check=True,cwd=HB,env=dict(os.environ,NODE_PATH=HB+'/node_modules'))
open(HB+'/build/tsconfig.json','w').write('{"compilerOptions":{"strict":true,"noEmit":true,"jsx":"react-jsx","module":"esnext","moduleResolution":"bundler","target":"es2022","lib":["es2022","dom"],"allowImportingTsExtensions":true,"skipLibCheck":true,"typeRoots":["../node_modules/@types"],"paths":{"grok/canvas":["./shim.tsx"],"react":["../node_modules/@types/react"],"react/*":["../node_modules/@types/react/*"],"react-dom/*":["../node_modules/@types/react-dom/*"]}},"files":["entry.tsx"]}')
tc=subprocess.run([HB+'/node_modules/.bin/tsc','-p',HB+'/build/tsconfig.json'],capture_output=True,text=True,cwd=HB)
if tc.returncode: print(tc.stdout[:3000]);sys.exit('tsc strict check FAILED')
assert 'dangerouslySetInnerHTML' not in src and 'fetch(' not in src and 'localStorage' not in src, 'canvas-forbidden construct in source'
html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bet Tracker canvas preview</title></head><body><div id="root"></div><script>'+open(HB+'/build/bundle.js').read().replace('</script','<\\/script')+'</script></body></html>'
open(P('preview.html'),'w').write(html)
# public web app (PWA): same component, web shim renders Page as the design header and Segmented as the bottom tab bar
open(HB+'/build/web.tsx','w').write('export { useState, useEffect, useMemo, useRef, Fragment } from "react";\nexport function Page(p: any){return (<><header className="top"><span>{p.title}</span><span className="pill">{String(p.summary||"").split(" \\u00b7 ")[0]}</span></header>{p.children}</>)}\nexport function Segmented(p: any){return (<nav className="tabs">{p.options.map((o: any)=>(<a key={o.value} href={"#"+o.value} data-v={o.value} className={p.value===o.value?"on":""} onClick={(e: any)=>{e.preventDefault();p.onChange(o.value);window.scrollTo(0,0)}}>{o.label}</a>))}</nav>)}\n')
subprocess.run([HB+'/node_modules/.bin/esbuild',HB+'/build/entry.tsx','--bundle','--jsx=automatic','--alias:grok/canvas='+HB+'/build/web.tsx','--define:process.env.NODE_ENV="production"','--minify','--outfile='+P('app.js')],check=True,cwd=HB,env=dict(os.environ,NODE_PATH=HB+'/node_modules'))
# EditCanvas batch vs what is live
edits=None
if os.path.exists(P('canvas.published.tsx')):
  old=open(P('canvas.published.tsx')).read().split('\n');new=src.split('\n')
  if old[:old.index('//<<DATA')]==new[:new.index('//<<DATA')] and old[old.index('//DATA>>'):]==new[new.index('//DATA>>'):]:
    edits=[]
    for op,a1,a2,b1,b2 in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
      if op=='equal':continue
      # anchor on the previous unchanged line so old_string is unique and non-empty
      edits.append({'old_string':'\n'.join(old[a1-1:a2]),'new_string':'\n'.join(old[a1-1:a1]+new[b1:b2])})
json.dump({'mode':'none' if edits==[] else 'edit' if edits else 'write','edits':edits or []},open(P('canvas_edits.json'),'w'),ensure_ascii=False,indent=1)
print(f"canvas.tsx {len(src)//1024}KB, {d['ticket_count']} tickets; canvas_edits.json mode={'none' if edits==[] else 'edit' if edits else 'write (full WriteCanvas)'}{' ('+str(len(edits))+' edits, '+str(sum(len(e['new_string']) for e in edits)//1024)+'KB)' if edits else ''}")

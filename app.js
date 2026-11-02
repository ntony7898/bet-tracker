// Markup mirrors Graphic's build_design.py; all visual decisions live in app.css.
const $=s=>document.querySelector(s),E=v=>String(v??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const tone=u=>{u=String(u);return u.startsWith('+')&&u!=='+0.00u'?'pos':u.startsWith('-')?'neg':'neu'};
const isNum=x=>typeof x==='number',fmt=x=>(x>=0?'+':'')+x.toFixed(2)+'u';
const RES={W:['WIN','win'],L:['LOSS','loss'],void:['VOID','push'],P:['PUSH','push'],'':['PENDING','pend']};
const LEG={hit:['WIN','win','✅'],miss:['LOSS','loss','❌'],pending:['PENDING','pend','⏳'],none:['NO MARK','none','–']};
const chip=(l,c)=>`<span class="chip ${c}">${l}</span>`;
const G={'fb':'<ellipse cx="12" cy="12" rx="10" ry="6" transform="rotate(-35 12 12)" fill="currentColor"/><path d="M9 15l6-6M10 11.5l2.5 2.5M11.5 10l2.5 2.5" stroke="#0B0F14" stroke-width="1.4" stroke-linecap="round"/>','puck':'<ellipse cx="12" cy="9" rx="9" ry="4" fill="currentColor"/><path d="M3 9v5c0 2.2 4 4 9 4s9-1.8 9-4V9c0 2.2-4 4-9 4S3 11.2 3 9z" fill="currentColor" opacity=".6"/>','base':'<circle cx="12" cy="12" r="9.5" fill="currentColor"/><path d="M7 4.5c2.5 2.5 2.5 12.5 0 15M17 4.5c-2.5 2.5-2.5 12.5 0 15" stroke="#B91C1C" stroke-width="1.4" fill="none"/>','bask':'<circle cx="12" cy="12" r="9.5" fill="currentColor"/><path d="M2.5 12h19M12 2.5v19M5.5 5.2c3 3 3 10.6 0 13.6M18.5 5.2c-3 3-3 10.6 0 13.6" stroke="#0B0F14" stroke-width="1.3" fill="none"/>','soc':'<circle cx="12" cy="12" r="9.5" fill="currentColor"/><path d="M12 8.2l3.6 2.6-1.4 4.2H9.8l-1.4-4.2z" fill="#0B0F14"/><path d="M12 8.2V3M15.6 10.8l4.6-1.6M14.2 15l2.8 4M9.8 15L7 19M8.4 10.8L3.8 9.2" stroke="#0B0F14" stroke-width="1.3"/>','multi':'<rect x="3" y="5" width="13" height="9" rx="2" fill="currentColor" opacity=".55"/><rect x="8" y="10" width="13" height="9" rx="2" fill="currentColor"/>','all':'<path d="M7 3h10v4a5 5 0 01-10 0zM5 4H3v2a3 3 0 003 3M19 4h2v2a3 3 0 01-3 3M10 13h4v3h-4zM8 18h8v3H8z" fill="currentColor"/>'};
const SPK={'NFL':'fb','NCAAF':'fb','CFB':'fb','NHL':'puck','MLB':'base','NBA':'bask','WNBA':'bask','SOCCER':'soc','EPL':'soc','MLS':'soc','MULTI':'multi','LADDER':'multi','ALL':'all'};
const ico=s=>`<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${G[SPK[String(s).toUpperCase()]||'multi']}</svg>`,scls=s=>'s-'+String(s).toUpperCase();
let D;
function ticket(t){const [lbl,c]=RES[t.result]||[E(t.result),'pend'];
 const legs=t.legs.length?`<ol class="legs">${t.legs.map(l=>{const [L,cc,m]=LEG[l.mark];return `<li class="leg ${cc}"><span class="mk">${m}</span><span class="lt">${E(l.text)}</span>${chip(L,cc)}</li>`}).join('')}</ol>`:'';
 const st=t['Stake (u)'],pr=t['Profit (u)'],prc=isNum(pr)&&pr>0?'pos':isNum(pr)&&pr<0?'neg':'';
 const meta=[['Stake',isNum(st)?st+'u':st?E(st):'—',''],['Odds',E(t.odds)||'—',''],['Result u',isNum(pr)?fmt(pr):'—',prc]];
 const extra=['implied','est'].filter(k=>t[k]).map(k=>`${k} ${E(t[k])}`).join(' · ');
 const tags=(t.tony_played==='Y'?'<span class="tag tp">Tony played</span>':'')+(t.favorite==='Y'?'<span class="tag fav">★ Favorite</span>':'');
 return `<article class="tk ${c} ${scls(t.sport)}"><div class="tkh"><span class="sp ${scls(t.sport)}">${ico(t.sport)}${E(t.sport)}</span><span class="gm">${E(t.game)}</span>${chip(lbl,c+' big')}</div>
<p class="pk">${E(t.title)}</p>${legs}<div class="meta">${meta.map(([k,v,cl])=>`<div class="${cl}"><b>${v}</b><i>${k}</i></div>`).join('')}</div>
<div class="foot">${tags}<span class="bk">${E(t.book)}${extra?' · '+extra:''}</span></div></article>`}
function banner(b){const p=b.split('|').map(s=>s.trim()),kv=[];let net=null;
 for(const s of p.slice(1)){const i=s.includes(':')?s.indexOf(':'):s.indexOf(' ');const k=s.slice(0,i).trim(),v=s.slice(i+1).trim();k==='Net'?net=v:kv.push([k,v])}
 const nv=net&&net.split(' ')[0],tn=nv?tone(nv):'neu';
 const big=net?`<div class="bn-net sb">${E(nv)}</div><div class="bn-sub">${E(net.slice(nv.length).trim()||'net units')}</div>`:'<div class="bn-net sm">no units</div><div class="bn-sub">before unit tracking</div>';
 return `<section class="bn sbd ${tn}"><div class="bn-d">${E(p[0])}</div>${big}<div class="bn-st">${kv.map(([k,v])=>`<div><b>${E(v)}</b><i>${E(k)}</i></div>`).join('')}</div></section>`}
const ucard=(u,cls='')=>`<div class="uc ${tone(u.net)} ${cls}"><div class="ul">${E(u.period)}</div><div class="uv">${E(u.net)}</div><div class="us">${E(u.settled)} settled · ${E(u.pending)} pending</div></div>`;
function rtable(title,head,rs,foot=''){return `<div class="rt"><h3>${E(title)}</h3>${rs.map(r=>`<div class="rg"><div class="rn">${E(r[0])}</div><div class="rcs">${head.map((h,i)=>`<div class="rc${h==='All'?' all':''} ${scls(h)}"><i>${h?ico(h):''}${E(h)}</i><b>${E(r[i+1])}</b></div>`).join('')}</div></div>`).join('')}${foot}</div>`}
const todayDate=()=>{const p=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Phoenix'}).format(new Date());return D.days.some(d=>d.date===p)?p:D.days[0].date};
function renderDays(){const td=todayDate();const f=$('#filter').value,q=$('#q').value.trim().toLowerCase();
 const one=d=>{const ts=d.tickets.filter(t=>(f==='all'||f==='played'&&t.tony_played==='Y'||f==='fav'&&t.favorite==='Y'||f==='pending'&&!t.result)&&(!q||(t.pick+' '+t.game+' '+t.sport).toLowerCase().includes(q)));
  if(!ts.length&&(f!=='all'||q))return'';return `<div class="day" id="d${d.date}">${banner(d.banner)}${ts.map(ticket).join('')}</div>`};
 const t=D.days.filter(d=>d.date===td).map(one).join(''),p=D.days.filter(d=>d.date!==td).map(one).join('');
 const html=(t?`<h2 class="h" id="today">Today</h2>${t}`:'')+(p?`<h2 class="h" id="past">Past picks</h2>${p}`:'');
 $('#days').innerHTML=html||'<p class="empty">No tickets match.</p>'}
function render(){const sports=D.record_header.slice(1),U=D.units,gt=U.find(u=>u.period==='Grand total');
 const months=U.filter(u=>!/^(Year|Grand)/.test(u.period)),years=U.filter(u=>u.period.startsWith('Year'));
 $('#pill').textContent=D.note;
 $('#summary-body').innerHTML=`<div class="note">${E(D.note)}</div><div class="hero ${tone(gt.net)}"><div class="ul">Grand total · ${E(D.units_label)}</div><div class="hv">${E(gt.net)}</div><div class="us">${gt.settled} settled · ${gt.pending} pending</div></div>
<div class="two">${ucard(months[0])}${ucard(years[0])}</div>${rtable('Overall record',sports,D.records.slice(0,1))}<h2 class="h">Today</h2>${banner(D.days.find(d=>d.date===todayDate()).banner)}<a class="cta" href="#today">Today's picks →</a><a class="cta" href="#past">Past picks →</a>`;
 $('#jump').innerHTML='<option value="">Jump to date</option>'+D.days.map(d=>`<option value="${d.date}">${E(d.label)}</option>`).join('');
 renderDays();$('#legend').textContent=D.legend;
 $('#totals-body').innerHTML='<h2 class="h">Grand total</h2>'+ucard(gt,'xl')+'<h2 class="h">Years</h2>'+years.map(y=>ucard(y,'xl')).join('')+'<h2 class="h">Months</h2>'+months.map(m=>ucard(m)).join('')+`<p class="legend">${E(D.units_label)}.</p>`;
 $('#records-body').innerHTML=rtable('All time',sports,D.records)+D.monthly.map(m=>rtable(m.month,m.cols,m.rows.filter(r=>r[0]),m.units?`<div class="rfoot ${tone(m.units.net)}"><span>Unit profit (Tony, from 10/28)</span><b>${E(m.units.net)}</b><em>${E(m.units.pending)}</em></div>`:'')).join('')+`<p class="legend">data ${E(D.version)}</p>`;
 if(location.hash){const h=location.hash;location.hash='';location.hash=h}}
$('#filter').onchange=$('#q').oninput=renderDays;
$('#jump').onchange=e=>{const v=e.target.value;if(!v)return;$('#filter').value='all';$('#q').value='';renderDays();location.hash='d'+v};
fetch('data.json',{cache:'no-store'}).then(r=>r.json()).then(j=>{D=j;render()}).catch(e=>$('#summary-body').textContent='Could not load data: '+e);
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js');

// Structure/behaviour only; all visual decisions are in app.css (classes + data-* attributes).
const $=s=>document.querySelector(s), esc=v=>String(v??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const sign=v=>/^\+/.test(v)&&!/^\+0\.00/.test(v)?'pos':/^-/.test(v)?'neg':'';
let D;
function table(cap,head,rows){return `<div class="table-wrap"><table><caption>${esc(cap)}</caption><thead><tr>${head.map(h=>`<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}
function ticket(t){const res=(t.result||'').toUpperCase()||'pending';
 return `<article class="ticket" data-result="${esc(res)}"><div class="ticket-top"><span>${esc(t.sport)} · ${esc(t.game)}</span><span>${esc(t.result||'Pending')}</span></div>
 <h3>${esc(t.title)}</h3>${t.legs.length?`<ul class="legs">${t.legs.map(l=>`<li class="leg" data-mark="${l.mark}">${esc(l.text)}</li>`).join('')}</ul>`:''}
 <div class="kv">${t.book?`<span>${esc(t.book)}</span>`:''}${t.odds?`<span>Odds <b>${esc(t.odds)}</b></span>`:''}${t.implied?`<span>Impl ${esc(t.implied)}</span>`:''}${t.est?`<span>Est ${esc(t.est)}</span>`:''}
 ${t['Stake (u)']!==''?`<span>Stake <b>${esc(t['Stake (u)'])}u</b></span>`:''}${t['Profit (u)']!==''?`<span>Profit <b class="${t['Profit (u)']>0?'pos':t['Profit (u)']<0?'neg':''}">${esc(t['Profit (u)'])}u</b></span>`:''}
 ${t.tony_played==='Y'?'<span class="tag">Tony played</span>':''}${t.favorite==='Y'?'<span class="tag">Favorite</span>':''}</div></article>`}
function renderDays(){const f=$('#filter').value,q=$('#q').value.toLowerCase();
 $('#days').innerHTML=D.days.map(d=>{const ts=d.tickets.filter(t=>(f==='all'||f==='played'&&t.tony_played==='Y'||f==='fav'&&t.favorite==='Y'||f==='pending'&&!t.result)&&(!q||(t.pick+' '+t.game).toLowerCase().includes(q)));
  if(!ts.length&&(f!=='all'||q))return'';
  return `<section class="day" id="d-${d.date}"><div class="day-banner"><h2>${esc(d.label)}</h2><div class="meta"><span>Day ${esc(d.day)}</span><span>Tony played ${esc(d.tony_played)}</span>${d.net?`<span>Net <b class="${sign(d.net)}">${esc(d.net)}</b></span><span>Running <b class="${sign(d.running)}">${esc(d.running)}</b></span>`:''}</div></div>${ts.map(ticket).join('')}</section>`}).join('')||'<p>No tickets match.</p>'}
function render(){const g=D.units.find(u=>u.period==='Grand total'),tp=D.records.find(r=>r[0]==='Tony played'),all=D.records[0];
 $('#summary').innerHTML=`<h1>Bet Tracker</h1><div class="stat-row"><div class="stat">Total units<b class="${sign(g.net)}">${esc(g.net)}</b></div><div class="stat">Tony played<b>${esc(tp[1])}</b></div><div class="stat">All picks<b>${esc(all[1])}</b></div></div><div class="note">${esc(D.note)} · ${g.settled} settled, ${g.pending} pending</div>`;
 $('#jump').innerHTML='<option value="">Jump to date</option>'+D.days.map(d=>`<option value="${d.date}">${esc(d.label)}</option>`).join('');
 renderDays();
 $('#view-units').innerHTML=table('Units (from 2026-10-28)',['Period','Net units','Settled','Pending'],D.units.map(u=>[u.period,u.net,u.settled,u.pending]));
 $('#view-records').innerHTML=table('Record',D.record_header,D.records)+D.monthly.map(m=>table(m.month,['',...m.cols],m.rows)+(m.units?`<p>Unit profit (Tony, from 10/28): <b class="${sign(m.units.net)}">${esc(m.units.net)}</b> ${esc(m.units.pending)}</p>`:'')).join('');
 $('#foot').textContent=D.legend+' · data '+D.version}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('is-active',x===b));document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!=='view-'+b.dataset.view)});
$('#filter').onchange=$('#q').oninput=renderDays;
$('#jump').onchange=e=>{if(e.target.value){$('#filter').value='all';$('#q').value='';renderDays();document.getElementById('d-'+e.target.value)?.scrollIntoView()}};
fetch('data.json',{cache:'no-store'}).then(r=>r.json()).then(j=>{D=j;render()}).catch(e=>$('#days').textContent='Could not load data: '+e);
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js');

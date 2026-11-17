#!/usr/bin/env python3
"""Interactive graph viewer. Writes out/graph.html (self-contained, no internet needed) and opens it.
  viz.py            build + open
  viz.py --no-open  build only
"""
import json, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graph
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Luma Event Graph</title>
<style>
:root{--bg:#fafaf8;--panel:#fff;--ink:#1c1c1a;--mute:#6b6b66;--line:#d9d8d2;--edge:#b9b8b0;
--booked:#1a7f4b;--requested:#b7791f;--seen:#4a6fa5;--skipped:#a7a7a0;--needs:#c0392b;--done:#0f5c36;
--topic:#7c4dbd;--host:#0e8a8a;--venue:#d2691e;--fb:#d6336c;--month:#7a5c3a}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15161a;--panel:#1e2026;--ink:#ecebe6;--mute:#9a9a94;--line:#33353d;--edge:#4a4c55;
--booked:#4cc38a;--requested:#e6b04a;--seen:#7da2d6;--skipped:#6d6d68;--needs:#f0675a;--done:#2fa36b;
--topic:#b38cf0;--host:#4fd1d1;--venue:#f39a5b;--fb:#f27aa6;--month:#c9a47a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif;display:flex;height:100vh;overflow:hidden}
#side{width:300px;max-width:42vw;background:var(--panel);border-right:1px solid var(--line);padding:16px;overflow:auto;flex:none}
h1{font-size:16px;margin:0 0 2px}.sub{color:var(--mute);font-size:12px;margin-bottom:12px}
h2{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:16px 0 6px}
label{display:flex;align-items:center;gap:8px;padding:2px 0;cursor:pointer}.dot{width:10px;height:10px;border-radius:50%;flex:none}
input[type=search]{width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
#stage{flex:1;position:relative;min-width:0}canvas{display:block;width:100%;height:100%;cursor:grab}
#info{position:absolute;right:12px;top:12px;width:300px;max-width:calc(100% - 24px);background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;display:none;max-height:70%;overflow:auto}
#info h3{margin:0 0 4px;font-size:14px}#info .k{color:var(--mute);font-size:12px}#info a{color:var(--seen)}
#info div.p{margin:4px 0;word-break:break-word}
#hint{position:absolute;left:12px;bottom:10px;color:var(--mute);font-size:12px}
@media (max-width:700px){body{flex-direction:column}#side{width:100%;max-width:none;max-height:38vh;border-right:0;border-bottom:1px solid var(--line)}}
</style></head><body>
<div id="side"><h1>Luma Event Graph</h1><div class="sub" id="stats"></div>
<input type="search" id="q" placeholder="Search title, topic, host…">
<h2>Events by status</h2><div id="fs"></div><h2>Other nodes</h2><div id="ft"></div>
<h2>Size = score / connections</h2></div>
<div id="stage"><canvas id="c"></canvas><div id="info"></div><div id="hint">Drag nodes · scroll to zoom · drag background to pan · click for details</div></div>
<script>
const DATA=__DATA__;
const css=n=>getComputedStyle(document.documentElement).getPropertyValue('--'+n).trim();
const STAT={booked:'booked',done:'done',requested:'requested',seen:'seen',skipped:'skipped',needs_user:'needs',awaiting_feedback:'requested'};
const TYPE={Topic:'topic',Host:'host',Venue:'venue',Feedback:'fb',MonthSummary:'month'};
const colorKey=n=>n.type==='Event'?(STAT[n.props.status]||'seen'):(TYPE[n.type]||'seen');
const nodes=DATA.nodes.filter(n=>n.type!=='Stats').map((n,i)=>({...n,x:Math.cos(i)*200+Math.random()*50,y:Math.sin(i)*200+Math.random()*50,vx:0,vy:0,deg:0}));
const idx=Object.fromEntries(nodes.map(n=>[n.id,n]));
const links=DATA.edges.filter(e=>idx[e.from]&&idx[e.to]).map(e=>({s:idx[e.from],t:idx[e.to],rel:e.rel}));
links.forEach(l=>{l.s.deg++;l.t.deg++});
const radius=n=>n.type==='Event'?5+Math.max(0,Number(n.props.score)||0)*.9:4+Math.min(n.deg,8)*1.2;
const hidden=new Set();let query='',sel=null,alpha=1;
const cv=document.getElementById('c'),ctx=cv.getContext('2d');let W,H,dpr=devicePixelRatio||1;
let view={x:0,y:0,k:1};
function resize(){const r=cv.getBoundingClientRect();W=r.width;H=r.height;cv.width=W*dpr;cv.height=H*dpr;view.x=W/2;view.y=H/2;alpha=Math.max(alpha,.3)}
addEventListener('resize',resize);resize();
const vis=n=>!hidden.has(n.type==='Event'?'s:'+(n.props.status||'seen'):'t:'+n.type)&&(!query||JSON.stringify(n).toLowerCase().includes(query)||false);
function tick(){const vn=nodes.filter(vis);
 for(let i=0;i<vn.length;i++){const a=vn[i];for(let j=i+1;j<vn.length;j++){const b=vn[j];let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy+.01;if(d2>90000)continue;const f=900/d2,d=Math.sqrt(d2);dx/=d;dy/=d;a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f}}
 for(const l of links){if(!vis(l.s)||!vis(l.t))continue;const dx=l.t.x-l.s.x,dy=l.t.y-l.s.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=(d-70)*.02;l.s.vx+=dx/d*f;l.s.vy+=dy/d*f;l.t.vx-=dx/d*f;l.t.vy-=dy/d*f}
 for(const n of vn){n.vx-=n.x*.004;n.vy-=n.y*.004;if(n.fx!=null){n.x=n.fx;n.y=n.fy;n.vx=n.vy=0}else{n.x+=n.vx*alpha;n.y+=n.vy*alpha}n.vx*=.6;n.vy*=.6}
 alpha=Math.max(alpha*.995,.02)}
function draw(){ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,H);ctx.translate(view.x,view.y);ctx.scale(view.k,view.k);
 const hi=sel?new Set([sel.id,...links.filter(l=>l.s===sel||l.t===sel).flatMap(l=>[l.s.id,l.t.id])]):null;
 ctx.lineWidth=1/view.k;
 for(const l of links){if(!vis(l.s)||!vis(l.t))continue;ctx.strokeStyle=css('edge');ctx.globalAlpha=hi?(hi.has(l.s.id)&&hi.has(l.t.id)?.9:.08):.45;ctx.beginPath();ctx.moveTo(l.s.x,l.s.y);ctx.lineTo(l.t.x,l.t.y);ctx.stroke()}
 for(const n of nodes){if(!vis(n))continue;ctx.globalAlpha=hi&&!hi.has(n.id)?.15:(n.props.status==='skipped'?.55:1);ctx.fillStyle=css(colorKey(n));
  ctx.beginPath();const r=radius(n);
  if(n.type==='Event')ctx.arc(n.x,n.y,r,0,7);else if(n.type==='MonthSummary')ctx.rect(n.x-r,n.y-r,2*r,2*r);else{ctx.moveTo(n.x,n.y-r);ctx.lineTo(n.x+r,n.y);ctx.lineTo(n.x,n.y+r);ctx.lineTo(n.x-r,n.y);ctx.closePath()}
  ctx.fill();if(n===sel){ctx.strokeStyle=css('ink');ctx.lineWidth=2/view.k;ctx.stroke();ctx.lineWidth=1/view.k}}
 ctx.globalAlpha=1;ctx.fillStyle=css('ink');ctx.font=(11/view.k)+'px system-ui';
 for(const n of nodes){if(!vis(n))continue;if(n.type==='Event'||n===sel||view.k>1.4){const t=label(n);ctx.fillText(t,n.x+radius(n)+3,n.y+4/view.k)}}}
const label=n=>{const t=n.props.title||n.id.replace(/^[a-z]+:/,'');return t.length>34?t.slice(0,33)+'…':t};
(function loop(){tick();draw();requestAnimationFrame(loop)})();
function world(e){const r=cv.getBoundingClientRect();return{x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k}}
function pick(p){let best=null;for(const n of nodes){if(!vis(n))continue;const r=radius(n)+3;if((n.x-p.x)**2+(n.y-p.y)**2<r*r)best=n}return best}
let drag=null,pan=null,moved=false;
cv.onpointerdown=e=>{cv.setPointerCapture(e.pointerId);moved=false;const p=world(e),n=pick(p);if(n){drag=n;n.fx=n.x;n.fy=n.y}else pan={x:e.clientX-view.x,y:e.clientY-view.y}};
cv.onpointermove=e=>{moved=true;if(drag){const p=world(e);drag.fx=p.x;drag.fy=p.y;alpha=.4}else if(pan){view.x=e.clientX-pan.x;view.y=e.clientY-pan.y}};
cv.onpointerup=e=>{if(drag){drag.fx=drag.fy=null;if(!moved)show(drag)}else if(!moved)show(null);drag=pan=null;cv.style.cursor='grab'};
cv.onwheel=e=>{e.preventDefault();const r=cv.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,k=Math.min(4,Math.max(.2,view.k*(e.deltaY<0?1.15:.87)));view.x=mx-(mx-view.x)*k/view.k;view.y=my-(my-view.y)*k/view.k;view.k=k};
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function show(n){sel=n;const el=document.getElementById('info');if(!n){el.style.display='none';return}
 const p=n.props,rel=links.filter(l=>l.s===n||l.t===n).map(l=>(l.s===n?l.rel+' → '+l.t.id:l.s.id+' → '+l.rel)).join('<br>');
 el.innerHTML='<h3>'+esc(p.title||n.id)+'</h3><div class="k">'+n.type+' · '+esc(n.id)+'</div>'+Object.entries(p).filter(([k])=>k!=='title').map(([k,v])=>'<div class="p"><span class="k">'+k+'</span> '+(k==='url'?'<a href="'+esc(v)+'" target="_blank" rel="noopener">'+esc(v)+'</a>':esc(typeof v==='object'?JSON.stringify(v):v))+'</div>').join('')+(rel?'<div class="k" style="margin-top:8px">Relations</div><div class="p">'+rel+'</div>':'');el.style.display='block'}
function legend(){const cnt=(f)=>nodes.filter(f).length;
 const sts=[...new Set(nodes.filter(n=>n.type==='Event').map(n=>n.props.status||'seen'))].sort();
 document.getElementById('fs').innerHTML=sts.map(s=>row('s:'+s,s,STAT[s]||'seen',cnt(n=>n.type==='Event'&&(n.props.status||'seen')===s))).join('')||'<span class="sub">no events yet</span>';
 const ts=[...new Set(nodes.filter(n=>n.type!=='Event').map(n=>n.type))].sort();
 document.getElementById('ft').innerHTML=ts.map(t=>row('t:'+t,t,TYPE[t]||'seen',cnt(n=>n.type===t))).join('')||'<span class="sub">none</span>';
 document.querySelectorAll('#side input[data-k]').forEach(i=>i.onchange=()=>{i.checked?hidden.delete(i.dataset.k):hidden.add(i.dataset.k);alpha=.5});
 document.getElementById('stats').textContent=nodes.length+' nodes · '+links.length+' edges';}
const row=(k,l,c,n)=>'<label><input type="checkbox" data-k="'+k+'" checked><span class="dot" style="background:var(--'+c+')"></span>'+l+' <span class="sub" style="margin:0 0 0 auto">'+n+'</span></label>';
legend();document.getElementById('q').oninput=e=>{query=e.target.value.toLowerCase().trim();alpha=.5};
</script></body></html>"""

def build():
    data = {"nodes": list(graph.nodes().values()), "edges": graph.edges()}
    out = os.path.join(ROOT, "out"); os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "graph.html")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    open(path, "w", encoding="utf-8").write(TEMPLATE.replace("__DATA__", payload))
    return path, len(data["nodes"]), len(data["edges"])

if __name__ == "__main__":
    p, n, e = build(); print(f"{p}  ({n} nodes, {e} edges)")
    if "--no-open" not in sys.argv: subprocess.run(["open", p])

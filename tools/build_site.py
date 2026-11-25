#!/usr/bin/env python3
"""Generate the Prime-agent catalog site (site/index.html).

Stdlib only. The output is a single self-contained HTML page (inline CSS
and JS, no external requests) organized around the collection's four
branches:

  Skills      vendored, categorized procedures (skills.json)
  MCP servers recommended tool servers, link-only (mcps.json)
  Sub-agents  delegable agent definitions, link-only (subagents.json)
  Void        vetted and valuable, deliberately not adopted (void.json)

Branch tabs switch sections, one search box filters every branch, and
the Skills branch keeps its category / tag / specials filters. All
counts are generated from the manifests. Run locally to preview, or let
the pages.yml workflow run it on manifest changes.

  python3 tools/build_site.py
"""
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "skills.json"
MCP_MANIFEST = ROOT / "mcps.json"
SUBAGENTS_MANIFEST = ROOT / "subagents.json"
PACKS_MANIFEST = ROOT / "packs.json"
TOOLS_MANIFEST = ROOT / "tools.json"
VOID_MANIFEST = ROOT / "void.json"
OUT = ROOT / "site" / "index.html"
REPO_URL = "https://github.com/ILIV007/Prime-agent"
CATEGORY_ORDER = ["development", "design", "marketing", "media", "research",
                  "security", "reverse-engineering", "cookbook"]
# One vivid accent per category and per branch: the catalog is colour-coded
# so a visitor can tell branches and categories apart at a glance.
CATEGORY_COLORS = {
    "development": "#22d3ee",
    "design": "#ff2e63",
    "marketing": "#ffd319",
    "media": "#a855f7",
    "research": "#22c55e",
    "security": "#f97316",
    "reverse-engineering": "#fb7185",
    "cookbook": "#f472b6",
}
BRANCH_COLORS = {
    "skills": "#22d3ee",
    "mcp": "#a855f7",
    "subagents": "#ff2e63",
    "tools": "#22c55e",
    "packs": "#ffd319",
    "void": "#7c8499",
}

CSS = """
:root{
  --bg:#0f1115; --panel:#171a21; --panel2:#1e222c; --line:#262c3a;
  --text:#e8ebf1; --muted:#a7aebe; --faint:#7c8499;
  --accent:#5ea8ff; --accent-ink:#0b1526; --gold:#e3b341; --radius:14px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.55;font-size:16px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
a:focus-visible,button:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 72px}
header.site{position:relative;overflow:hidden;padding:64px 20px 14px;text-align:center;
  background:
    radial-gradient(640px 260px at 12% 0%,rgba(255,46,99,.22),transparent 60%),
    radial-gradient(720px 280px at 88% 8%,rgba(34,211,238,.20),transparent 60%),
    radial-gradient(560px 320px at 50% 115%,rgba(168,85,247,.22),transparent 60%),
    linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px),
    #11141c;
  background-size:auto,auto,auto,26px 26px,26px 26px,auto;
  border-bottom:1px solid var(--line)}
#hero3d{position:absolute;inset:0;width:100%;height:100%;display:block;opacity:.6}
header.site>*{position:relative;z-index:1}
.kicker{color:#ffd319;font-size:.82rem;letter-spacing:.14em;text-transform:uppercase;margin:0 0 10px;font-weight:700}
h1{font-size:2.7rem;line-height:1.15;margin:0 0 12px;font-weight:800;letter-spacing:-.01em;
  background:linear-gradient(92deg,#22d3ee,#a855f7 45%,#ff2e63 75%,#ffd319);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.tagline{color:var(--muted);max-width:680px;margin:0 auto;font-size:1.05rem}
.stats{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:26px auto 4px}
.stat{background:rgba(23,26,33,.85);border:1px solid var(--line);border-radius:999px;
  padding:7px 16px;font-size:.92rem;color:var(--muted)}
.stat::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;
  background:var(--c,var(--accent));margin-right:8px;box-shadow:0 0 8px var(--c,var(--accent))}
.stat b{color:var(--text);font-weight:700}
.toolbar{position:sticky;top:0;z-index:5;background:rgba(15,17,21,.94);
  backdrop-filter:blur(6px);border-bottom:1px solid var(--line);
  padding:14px 0 12px;margin-top:26px}
.tabs{display:flex;gap:8px;flex-wrap:wrap}
.tab{appearance:none;border:1px solid var(--line);background:var(--panel);
  color:var(--muted);border-radius:999px;padding:8px 16px;font-size:.95rem;
  font-weight:600;cursor:pointer;font-family:inherit}
.tab:hover{color:var(--text);border-color:var(--faint)}
.tab[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.tab[data-branch="skills"][aria-pressed="true"]{background:#22d3ee;border-color:#22d3ee}
.tab[data-branch="mcp"][aria-pressed="true"]{background:#a855f7;border-color:#a855f7;color:#fff}
.tab[data-branch="subagents"][aria-pressed="true"]{background:#ff2e63;border-color:#ff2e63;color:#fff}
.tab[data-branch="tools"][aria-pressed="true"]{background:#22c55e;border-color:#22c55e}
.tab[data-branch="void"][aria-pressed="true"]{background:#7c8499;border-color:#7c8499;color:#fff}
.tab .n{opacity:.75;font-size:.85em;margin-left:5px}
#search{width:100%;margin-top:12px;padding:12px 16px;font-size:1rem;color:var(--text);
  background:var(--panel);border:1px solid var(--line);border-radius:10px;outline:none}
#search:focus{border-color:var(--accent)}
section.branch{margin-top:44px}
.branch-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.branch-head h2{font-size:1.45rem;margin:0;font-weight:700}
.branch-head h2::before{content:"";display:inline-block;width:11px;height:11px;border-radius:3px;
  background:var(--bc,var(--accent));margin-right:10px;box-shadow:0 0 10px var(--bc,var(--accent));
  transform:rotate(45deg)}
section.branch[data-branch="skills"]{--bc:#22d3ee}
section.branch[data-branch="mcp"]{--bc:#a855f7}
section.branch[data-branch="subagents"]{--bc:#ff2e63}
section.branch[data-branch="tools"]{--bc:#22c55e}
section.branch[data-branch="packs"]{--bc:#ffd319}
section.branch[data-branch="void"]{--bc:#7c8499}
.branch-head .shown{color:var(--faint);font-size:.9rem}
.branch-note{color:var(--muted);max-width:780px;margin:8px 0 0}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;align-items:center}
.filters .lbl{color:var(--faint);font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;margin-right:2px}
.chip{appearance:none;border:1px solid var(--line);background:var(--panel);
  color:var(--muted);border-radius:999px;padding:5px 12px;font-size:.87rem;
  font-weight:600;cursor:pointer;font-family:inherit}
.chip:hover{color:var(--text)}
.chip[aria-pressed="true"]{background:var(--text);border-color:var(--text);color:var(--bg)}
.chip .n{opacity:.7;font-size:.85em;margin-left:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin-top:18px}
.card{position:relative;background:linear-gradient(180deg,var(--panel2),var(--panel) 55%);
  border:1px solid var(--line);border-radius:var(--radius);
  padding:20px 18px 18px;display:flex;flex-direction:column;gap:8px;overflow:hidden;
  transform-style:preserve-3d;will-change:transform;
  transition:border-color .18s ease,box-shadow .18s ease}
.card::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;
  background:linear-gradient(90deg,var(--catc,var(--accent)),transparent 85%)}
.card:hover{border-color:var(--catc,var(--faint));
  box-shadow:0 14px 34px rgba(0,0,0,.45),0 0 0 1px var(--catc,var(--line)),0 0 22px -6px var(--catc,var(--accent))}
.card h3{margin:0;font-size:1.08rem;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.badge{font-size:.68rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
  padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.badge.cat{background:var(--panel2);color:var(--text)}
.badge.star{background:var(--gold);border-color:var(--gold);color:#241a02}
.badge.paid{color:var(--gold);border-color:var(--gold)}
.desc{margin:0}
.why{margin:0;color:var(--muted);font-size:.93rem}
.meta{display:flex;flex-wrap:wrap;gap:6px 14px;color:var(--faint);font-size:.85rem}
.access{background:var(--panel2);border:1px solid var(--line);border-radius:10px;
  padding:10px 12px;font-size:.9rem;color:var(--muted)}
.access b{color:var(--text);font-weight:650}
.chips-inline{display:flex;flex-wrap:wrap;gap:6px}
.chips-inline span{background:var(--panel2);border:1px solid var(--line);border-radius:999px;
  padding:1px 9px;font-size:.78rem;color:var(--muted)}
.tag{background:none;border:1px solid var(--line);border-radius:999px;color:var(--accent);
  padding:1px 9px;font-size:.78rem;cursor:pointer;font-family:inherit}
.tag:hover{border-color:var(--accent)}
.card footer{margin-top:auto;padding-top:6px;font-size:.92rem;display:flex;gap:16px}
.void .card{background:transparent;border-style:dashed}
.empty-note{display:none;color:var(--muted);padding:28px 0 4px}
.site-footer{margin-top:64px;text-align:center;color:var(--faint);font-size:.88rem}
.card h3,.desc,.why,.access{overflow-wrap:anywhere}
@media (max-width:560px){
  h1{font-size:1.8rem}
  .grid{grid-template-columns:1fr}
  .tabs{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;padding-bottom:4px}
  .tabs::-webkit-scrollbar{display:none}
  .tab{flex:0 0 auto;white-space:nowrap}
  .toolbar{position:static}
}
"""

JS = """
const search=document.getElementById('search');
const tabs=[...document.querySelectorAll('.tab[data-branch]')];
const sections=[...document.querySelectorAll('section.branch')];
const cards=[...document.querySelectorAll('.card')];
const catChips=[...document.querySelectorAll('.chip[data-cat]')];
const tagChips=[...document.querySelectorAll('.chip[data-tag]')];
const specialChip=document.getElementById('chip-special');
let branch='all', cat='all', tag=null, specialOnly=false;
function apply(){
  const q=search.value.trim().toLowerCase();
  for(const s of sections){
    const inBranch=branch==='all'||s.dataset.branch===branch;
    let shown=0;
    for(const c of s.querySelectorAll('.card')){
      const okQ=!q||c.dataset.search.includes(q);
      let okF=true;
      if(c.dataset.branch==='skills'){
        okF=(cat==='all'||c.dataset.category===cat)
          &&(!tag||(c.dataset.tags||'').split(' ').includes(tag))
          &&(!specialOnly||c.dataset.special==='1');
      }
      const show=inBranch&&okQ&&okF;
      c.style.display=show?'':'none';
      if(show)shown++;
    }
    s.style.display=(inBranch&&shown>0)?'':'none';
    const el=s.querySelector('.shown');
    if(el) el.textContent=shown+' shown';
    const empty=s.querySelector('.empty-note');
    if(empty) empty.style.display=(inBranch&&shown===0)?'block':'none';
    if(inBranch&&shown===0&&q) s.style.display='';
  }
}
search.addEventListener('input',apply);
for(const t of tabs){
  t.addEventListener('click',()=>{
    tabs.forEach(x=>x.setAttribute('aria-pressed','false'));
    t.setAttribute('aria-pressed','true');
    branch=t.dataset.branch;
    apply();
  });
}
for(const ch of catChips){
  ch.addEventListener('click',()=>{
    catChips.forEach(x=>x.setAttribute('aria-pressed','false'));
    ch.setAttribute('aria-pressed','true');
    cat=ch.dataset.cat;
    apply();
  });
}
for(const ch of tagChips){
  ch.addEventListener('click',()=>{
    if(tag===ch.dataset.tag){tag=null;ch.setAttribute('aria-pressed','false');}
    else{
      tagChips.forEach(x=>x.setAttribute('aria-pressed','false'));
      ch.setAttribute('aria-pressed','true');
      tag=ch.dataset.tag;
    }
    apply();
  });
}
if(specialChip){
  specialChip.addEventListener('click',()=>{
    specialOnly=!specialOnly;
    specialChip.setAttribute('aria-pressed',String(specialOnly));
    apply();
  });
}
for(const t of document.querySelectorAll('.card .tag')){
  t.addEventListener('click',()=>{
    const skillsTab=tabs.find(x=>x.dataset.branch==='skills');
    if(skillsTab&&branch!=='skills') skillsTab.click();
    const chip=tagChips.find(x=>x.dataset.tag===t.dataset.tag);
    if(chip&&tag!==t.dataset.tag) chip.click();
    document.querySelector('.toolbar').scrollIntoView({behavior:'smooth'});
  });
}
apply();

/* --- 3D hero: rotating wireframe cubes + particles, vanilla canvas --- */
(function(){
  const canvas=document.getElementById('hero3d');
  if(!canvas) return;
  const ctx=canvas.getContext('2d');
  if(!ctx) return;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const COLORS=['#22d3ee','#a855f7','#ff2e63','#ffd319','#22c55e','#f97316'];
  const V=[[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]];
  const E=[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
  let seed=11;
  const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
  const cubes=[];
  for(let i=0;i<16;i++){
    cubes.push({x:(rnd()-0.5)*9,y:(rnd()-0.5)*3.4,z:rnd()*3-1,s:0.28+rnd()*0.5,
      c:COLORS[i%COLORS.length],ph:rnd()*6.28,sp:0.5+rnd()});
  }
  const dots=[];
  for(let i=0;i<70;i++) dots.push({x:rnd(),y:rnd(),r:0.6+rnd()*1.6,c:COLORS[i%COLORS.length],ph:rnd()*6.28});
  let W=0,H=0,mx=0,my=0,tx=0,ty=0,t=0,visible=true;
  function resize(){
    const r=canvas.getBoundingClientRect();
    W=canvas.width=Math.max(2,Math.round(r.width));
    H=canvas.height=Math.max(2,Math.round(r.height));
  }
  function project(x,y,z){
    const f=5.2/(5.2+z+3);
    return [W/2+x*f*H*0.42, H/2+y*f*H*0.42, f];
  }
  function draw(){
    ctx.clearRect(0,0,W,H);
    tx+=(mx-tx)*0.05; ty+=(my-ty)*0.05;
    const ay=t*0.45+tx*0.8, ax=0.55+ty*0.4;
    const cy=Math.cos(ay),sy=Math.sin(ay),cx=Math.cos(ax),sx=Math.sin(ax);
    for(const d of dots){
      const tw=0.35+0.3*Math.sin(t*1.4+d.ph);
      ctx.globalAlpha=tw;
      ctx.fillStyle=d.c;
      ctx.beginPath();
      ctx.arc(d.x*W,d.y*H,d.r,0,6.29);
      ctx.fill();
    }
    ctx.globalAlpha=1;
    for(const cube of cubes){
      const bob=Math.sin(t*cube.sp+cube.ph)*0.14;
      const pts=V.map(([x,y,z])=>{
        let X=x*cube.s,Y=y*cube.s,Z=z*cube.s;
        let X1=X*cy+Z*sy, Z1=-X*sy+Z*cy;
        let Y1=Y*cx-Z1*sx, Z2=Y*sx+Z1*cx;
        return project(X1+cube.x, Y1+cube.y+bob, Z2+cube.z);
      });
      ctx.strokeStyle=cube.c;
      ctx.lineWidth=1.4;
      ctx.globalAlpha=0.85;
      ctx.beginPath();
      for(const [a,b] of E){ ctx.moveTo(pts[a][0],pts[a][1]); ctx.lineTo(pts[b][0],pts[b][1]); }
      ctx.stroke();
    }
    ctx.globalAlpha=1;
  }
  function frame(){
    if(visible){ t+=0.012; draw(); }
    if(!reduced) requestAnimationFrame(frame);
  }
  window.addEventListener('pointermove',e=>{
    mx=e.clientX/window.innerWidth-0.5;
    my=e.clientY/window.innerHeight-0.5;
  },{passive:true});
  window.addEventListener('resize',()=>{ resize(); draw(); });
  if('IntersectionObserver' in window){
    new IntersectionObserver(en=>{ visible=en[0].isIntersecting; },{threshold:0.02}).observe(canvas);
  }
  resize();
  draw();
  if(!reduced) requestAnimationFrame(frame);
})();

/* --- Card tilt: subtle 3D lean toward the pointer --- */
(function(){
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if(!window.matchMedia('(pointer: fine)').matches) return;
  for(const card of document.querySelectorAll('.card')){
    card.addEventListener('pointermove',e=>{
      const r=card.getBoundingClientRect();
      const px=(e.clientX-r.left)/r.width-0.5;
      const py=(e.clientY-r.top)/r.height-0.5;
      card.style.transform=`perspective(900px) rotateX(${(-py*6).toFixed(2)}deg) rotateY(${(px*7).toFixed(2)}deg) translateY(-3px)`;
    });
    card.addEventListener('pointerleave',()=>{ card.style.transform=''; });
  }
})();
"""


def esc(value):
    return html.escape(str(value), quote=True)


def stars_txt(entry):
    stars = entry.get("stars_at_import")
    return f"{stars:,}" if isinstance(stars, int) else "—"


def license_txt(entry):
    lic = entry.get("license") or "—"
    return "no license declared" if lic == "none" else lic


def source_url(skill):
    src = skill.get("source") or {}
    url = src.get("url") or REPO_URL
    commit = src.get("commit")
    path = (src.get("path") or "").strip("/")
    # Website sources have commit "n/a" (no repo to pin) — link straight
    # to the site instead of building a dead /tree/n/a/... URL.
    if commit and commit != "n/a":
        url = f"{url}/tree/{commit}"
        if path and path != ".":
            url = f"{url}/{path}"
    return url


def folder_url(skill):
    return f"{REPO_URL}/tree/main/categories/{skill.get('category')}/{skill.get('name')}"


def search_blob(*parts):
    return esc(" ".join(str(p or "") for p in parts).lower())


def skill_card(skill):
    name = skill.get("title") or skill.get("name") or ""
    category = skill.get("category") or ""
    link_only = skill.get("entry") == "link-only"
    special = bool(skill.get("special"))
    tags = skill.get("tags") or []
    requires = skill.get("requires") or []
    badges = f'<span class="badge cat">{esc(category)}</span>'
    if special:
        badges += '<span class="badge star">⭐ special</span>'
    if link_only:
        badges += '<span class="badge">link-only</span>'
    req_html = ""
    if requires:
        req_html = ('<div class="chips-inline">' +
                    "".join(f"<span>{esc(r)}</span>" for r in requires) + "</div>")
    tags_html = ""
    if tags:
        tags_html = ('<div class="chips-inline">' +
                     "".join(f'<button class="tag" data-tag="{esc(t)}">#{esc(t)}</button>'
                             for t in tags) + "</div>")
    blob = search_blob(skill.get("name"), name, skill.get("description"),
                       skill.get("why"), category, " ".join(tags),
                       "special" if special else "",
                       (skill.get("source") or {}).get("repo"))
    color = CATEGORY_COLORS.get(category, BRANCH_COLORS["skills"])
    return f"""<article class="card" style="--catc:{color}" data-branch="skills" data-category="{esc(category)}" data-tags="{esc(' '.join(tags))}" data-special="{'1' if special else ''}" data-search="{blob}">
  <h3>{esc(name)} {badges}</h3>
  <p class="desc">{esc(skill.get('description') or '')}</p>
  <p class="why">{esc(skill.get('why') or '')}</p>
  <div class="meta"><span>License: {esc(license_txt(skill))}</span><span>★ {esc(stars_txt(skill))} at import</span></div>
  {req_html}
  {tags_html}
  <footer><a href="{esc(folder_url(skill))}" target="_blank" rel="noopener">Files ↗</a><a href="{esc(source_url(skill))}" target="_blank" rel="noopener">Source ↗</a></footer>
</article>"""


def shelf_card(entry, branch, meta_parts, access_label):
    """Shared card for the link-only shelves (MCP servers, sub-agents)."""
    src = entry.get("source") or {}
    url = src.get("url") or REPO_URL
    name = entry.get("title") or entry.get("name") or ""
    badges = ""
    if entry.get("paid"):
        badges = f'<span class="badge paid">{esc(entry["paid"])}</span>'
    meta = " · ".join(x for x in meta_parts if x)
    blob = search_blob(entry.get("name"), name, entry.get("description"),
                       entry.get("why"), meta, src.get("repo"))
    return f"""<article class="card" style="--catc:{BRANCH_COLORS.get(branch, '#5ea8ff')}" data-branch="{branch}" data-search="{blob}">
  <h3>{esc(name)} {badges}</h3>
  <p class="desc">{esc(entry.get('description') or '')}</p>
  <p class="why">{esc(entry.get('why') or '')}</p>
  <div class="meta"><span>{esc(meta)}</span><span>License: {esc(license_txt(entry))}</span><span>★ {esc(stars_txt(entry))} at import</span></div>
  <div class="access"><b>{esc(access_label)}:</b> {esc(entry.get('access') or '')}</div>
  <footer><a href="{esc(url)}" target="_blank" rel="noopener">Source ↗</a></footer>
</article>"""


def void_card(entry):
    src = entry.get("source") or {}
    url = src.get("url") or REPO_URL
    name = entry.get("title") or entry.get("name") or ""
    blob = search_blob(entry.get("name"), name, entry.get("description"),
                       entry.get("why_valuable"), entry.get("why_not_included"),
                       src.get("repo"))
    return f"""<article class="card" style="--catc:{BRANCH_COLORS['void']}" data-branch="void" data-search="{blob}">
  <h3>{esc(name)}</h3>
  <p class="desc">{esc(entry.get('description') or '')}</p>
  <p class="why"><b>Why it's valuable:</b> {esc(entry.get('why_valuable') or '')}</p>
  <p class="why"><b>Why it's not in the collection:</b> {esc(entry.get('why_not_included') or '')}</p>
  <div class="meta"><span>License: {esc(license_txt(entry))}</span><span>★ {esc(stars_txt(entry))} at import</span></div>
  <footer><a href="{esc(url)}" target="_blank" rel="noopener">Source ↗</a></footer>
</article>"""


def pack_card(pack, lookups):
    """A pack card: the job, why this set, and its entries grouped by branch."""
    name = pack.get("title") or pack.get("name") or ""
    groups = []
    blob_parts = [pack.get("name"), name, pack.get("description"), pack.get("why")]
    for branch, label in (("skills", "Skills"), ("mcp", "MCP"), ("subagents", "Sub-agents"), ("tools", "Tools")):
        links = []
        for ref in pack.get("entries") or []:
            if ref.get("branch") != branch:
                continue
            entry = lookups[branch].get(ref.get("name")) or {}
            title = entry.get("title") or ref.get("name") or ""
            blob_parts.append(ref.get("name"))
            if branch == "skills":
                url = folder_url(entry) if entry else REPO_URL
            else:
                url = (entry.get("source") or {}).get("url") or REPO_URL
            links.append(f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(title)}</a>')
        if links:
            groups.append(f'<p class="why"><b>{label}:</b> {", ".join(links)}</p>')
    return f"""<article class="card" style="--catc:{BRANCH_COLORS['packs']}" data-branch="packs" data-search="{search_blob(*blob_parts)}">
  <h3>{esc(name)}</h3>
  <p class="desc">{esc(pack.get('description') or '')}</p>
  <p class="why">{esc(pack.get('why') or '')}</p>
  {''.join(groups)}
</article>"""


def branch_section(branch, title, note, cards_html, extra=""):
    return f"""<section class="branch{' void' if branch == 'void' else ''}" data-branch="{branch}" id="{branch}">
  <div class="branch-head"><h2>{esc(title)}</h2><span class="shown"></span></div>
  <p class="branch-note">{note}</p>
  {extra}
  <div class="grid">
{cards_html}
  </div>
  <p class="empty-note">Nothing here matches the current search or filters.</p>
</section>"""


def load_list(path, key):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get(key) or []


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    skills = data["skills"]
    mcp_servers = load_list(MCP_MANIFEST, "servers")
    subagents = load_list(SUBAGENTS_MANIFEST, "agents")
    void_entries = load_list(VOID_MANIFEST, "entries")
    packs = load_list(PACKS_MANIFEST, "packs")
    tools = load_list(TOOLS_MANIFEST, "tools")
    total = data.get("count", len(skills))
    link_only_count = sum(1 for s in skills if s.get("entry") == "link-only")
    special_count = sum(1 for s in skills if s.get("special"))

    counts = Counter(s.get("category") or "" for s in skills)
    ordered = [c for c in CATEGORY_ORDER if c in counts]
    ordered += sorted(c for c in counts if c not in ordered)

    cat_chips = [f'<button class="chip" data-cat="all" aria-pressed="true">All'
                 f'<span class="n">{total}</span></button>']
    for c in ordered:
        cat_chips.append(f'<button class="chip" data-cat="{esc(c)}" aria-pressed="false">{esc(c)}'
                         f'<span class="n">{counts[c]}</span></button>')
    cat_chips.append(f'<button class="chip" id="chip-special" aria-pressed="false">⭐ Specials'
                     f'<span class="n">{special_count}</span></button>')

    tag_counts = Counter(t for s in skills for t in (s.get("tags") or []))
    tag_chips = [f'<button class="chip" data-tag="{esc(t)}" aria-pressed="false">#{esc(t)}'
                 f'<span class="n">{n}</span></button>'
                 for t, n in sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))]

    by_cat = {}
    for s in skills:
        by_cat.setdefault(s.get("category") or "", []).append(s)
    skill_cards = []
    for c in ordered:
        for s in sorted(by_cat[c], key=lambda x: (x.get("name") or "").lower()):
            skill_cards.append(skill_card(s))

    skill_filters = f"""<div class="filters"><span class="lbl">Category</span>{''.join(cat_chips)}</div>
  <div class="filters"><span class="lbl">Tags</span>{''.join(tag_chips)}</div>"""

    mcp_cards = [shelf_card(srv, "mcp",
                            [" + ".join(srv.get("transport") or []),
                             ", ".join(srv.get("requires") or [])],
                            "Access")
                 for srv in sorted(mcp_servers, key=lambda s: (s.get("name") or "").lower())]
    agent_cards = [shelf_card(agent, "subagents",
                              [str(agent.get("kind") or ""),
                               ", ".join(agent.get("harnesses") or [])],
                              "Tools / permissions")
                   for agent in sorted(subagents, key=lambda a: (a.get("name") or "").lower())]
    void_cards = [void_card(e) for e in
                  sorted(void_entries, key=lambda e: (e.get("name") or "").lower())]

    lookups = {
        "skills": {s.get("name"): s for s in skills},
        "mcp": {s.get("name"): s for s in mcp_servers},
        "subagents": {a.get("name"): a for a in subagents},
        "tools": {t.get("name"): t for t in tools},
    }
    pack_cards = [pack_card(p, lookups) for p in
                  sorted(packs, key=lambda p: (p.get("name") or "").lower())]

    tool_cards = [shelf_card(tool, "tools",
                             [str(tool.get("kind") or "")],
                             "Access")
                  for tool in sorted(tools, key=lambda t: (t.get("name") or "").lower())]

    tabs = [("all", "All branches", total + len(mcp_servers) + len(subagents) + len(tools) + len(void_entries)),
            ("skills", "Skills", total),
            ("mcp", "MCP servers", len(mcp_servers)),
            ("subagents", "Sub-agents", len(subagents)),
            ("tools", "Tools", len(tools)),
            ("void", "Void", len(void_entries))]
    tabs_html = "".join(
        f'<button class="tab" data-branch="{b}" aria-pressed="{"true" if b == "all" else "false"}">'
        f'{esc(label)}<span class="n">{n}</span></button>'
        for b, label, n in tabs)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prime-agent — skills, MCP servers and sub-agents for AI agents</title>
<meta name="description" content="Prime-agent: a curated collection of agent skills, recommended MCP servers and delegable sub-agents — one representative per capability, vetted and categorized.">
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <canvas id="hero3d" aria-hidden="true"></canvas>
  <p class="kicker">Curated for AI agents</p>
  <h1>Prime-agent</h1>
  <p class="tagline">Skills tell an agent how to work, MCP servers give it hands, sub-agents give it a team. One vetted representative per capability — no duplicates, every entry licence-checked.</p>
  <div class="stats">
    <span class="stat" style="--c:#22d3ee"><b>{total}</b> skills</span>
    <span class="stat" style="--c:#a855f7"><b>{len(mcp_servers)}</b> MCP servers</span>
    <span class="stat" style="--c:#ff2e63"><b>{len(subagents)}</b> sub-agents</span>
    <span class="stat" style="--c:#22c55e"><b>{len(tools)}</b> tools</span>
    <span class="stat" style="--c:#7c8499"><b>{len(void_entries)}</b> Void entries</span>
    <span class="stat" style="--c:#ffd319"><b>{len(packs)}</b> packs</span>
    <span class="stat" style="--c:#e3b341"><b>{special_count}</b> ⭐ specials</span>
  </div>
</header>
<div class="wrap">
<div class="toolbar">
  <div class="tabs" role="group" aria-label="Collection branches">{tabs_html}</div>
  <input id="search" type="search" placeholder="Search every branch — names, descriptions, tags, sources…" aria-label="Search the collection">
</div>
<main>
{branch_section("packs", "Packs",
    "Curated cross-branch sets for one job — references only, no new entries. "
    f'Every reference is validated against its branch manifest. Full list in <a href="{REPO_URL}/blob/main/packs.json">packs.json</a>.',
    "".join(pack_cards))}
{branch_section("skills", "Skills",
    "Vendored procedures an agent can load and follow, categorized by function. "
    "“Link-only” entries carry metadata and a source link only, because their licence does not permit redistribution.",
    "".join(skill_cards), skill_filters)}
{branch_section("mcp", "MCP servers",
    "Recommended tool servers, not skills — link-only, nothing vendored. "
    f'Every entry states what the server can run or access; paid services are labelled. Full list in <a href="{REPO_URL}/blob/main/mcps.json">mcps.json</a>.',
    "".join(mcp_cards))}
{branch_section("subagents", "Sub-agents",
    "Delegable agent definitions with their own context, role and tool scope — link-only, nothing vendored. "
    f'Every entry states the tools and permissions the agent expects. Full list in <a href="{REPO_URL}/blob/main/subagents.json">subagents.json</a>.',
    "".join(agent_cards))}
{branch_section("tools", "Tools",
    "Standalone utilities an agent picks up directly — link-only, nothing vendored. "
    f'Every entry states what it runs, reaches, or costs; paid services are labelled. Full list in <a href="{REPO_URL}/blob/main/tools.json">tools.json</a>.',
    "".join(tool_cards))}
{branch_section("void", "Void",
    "Vetted, valuable, not adopted — link-only, and <b>not skills</b>: platforms, plugins or infrastructure that do not belong in the collection, "
    f'or duplicates of an entry that already exists. Full list in <a href="{REPO_URL}/blob/main/void.json">void.json</a>.',
    "".join(void_cards))}
</main>
<p class="site-footer">Generated from <a href="{REPO_URL}/blob/main/skills.json">skills.json</a>, <a href="{REPO_URL}/blob/main/mcps.json">mcps.json</a>, <a href="{REPO_URL}/blob/main/subagents.json">subagents.json</a> and <a href="{REPO_URL}/blob/main/void.json">void.json</a> · <a href="{REPO_URL}">View the repository on GitHub</a></p>
</div>
<script>{JS}</script>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT} ({total} skills, {special_count} specials, {link_only_count} link-only, {len(tag_counts)} tags, {len(mcp_servers)} MCP servers, {len(subagents)} sub-agents, {len(tools)} tools, {len(void_entries)} Void entries, {len(packs)} packs)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the Prime Skill catalog site (site/index.html).

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
VOID_MANIFEST = ROOT / "void.json"
OUT = ROOT / "site" / "index.html"
REPO_URL = "https://github.com/ILIV007/prime-skill"
CATEGORY_ORDER = ["development", "design", "marketing", "media", "research",
                  "security", "reverse-engineering", "cookbook"]

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
header.site{padding:56px 20px 8px;text-align:center}
.kicker{color:var(--faint);font-size:.82rem;letter-spacing:.14em;text-transform:uppercase;margin:0 0 10px}
h1{font-size:2.4rem;line-height:1.15;margin:0 0 12px;font-weight:750;letter-spacing:-.01em}
.tagline{color:var(--muted);max-width:680px;margin:0 auto;font-size:1.05rem}
.stats{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin:26px auto 4px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:999px;
  padding:7px 16px;font-size:.92rem;color:var(--muted)}
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
.tab .n{opacity:.75;font-size:.85em;margin-left:5px}
#search{width:100%;margin-top:12px;padding:12px 16px;font-size:1rem;color:var(--text);
  background:var(--panel);border:1px solid var(--line);border-radius:10px;outline:none}
#search:focus{border-color:var(--accent)}
section.branch{margin-top:44px}
.branch-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.branch-head h2{font-size:1.45rem;margin:0;font-weight:700}
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
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:18px;display:flex;flex-direction:column;gap:8px}
.card:hover{border-color:var(--faint)}
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
    return f"""<article class="card" data-branch="skills" data-category="{esc(category)}" data-tags="{esc(' '.join(tags))}" data-special="{'1' if special else ''}" data-search="{blob}">
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
    return f"""<article class="card" data-branch="{branch}" data-search="{blob}">
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
    return f"""<article class="card" data-branch="void" data-search="{blob}">
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
    for branch, label in (("skills", "Skills"), ("mcp", "MCP"), ("subagents", "Sub-agents")):
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
    return f"""<article class="card" data-branch="packs" data-search="{search_blob(*blob_parts)}">
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
    }
    pack_cards = [pack_card(p, lookups) for p in
                  sorted(packs, key=lambda p: (p.get("name") or "").lower())]

    tabs = [("all", "All branches", total + len(mcp_servers) + len(subagents) + len(void_entries)),
            ("skills", "Skills", total),
            ("mcp", "MCP servers", len(mcp_servers)),
            ("subagents", "Sub-agents", len(subagents)),
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
<title>Prime Skill — skills, MCP servers and sub-agents for AI agents</title>
<meta name="description" content="Prime Skill: a curated collection of agent skills, recommended MCP servers and delegable sub-agents — one representative per capability, vetted and categorized.">
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <p class="kicker">Curated for AI agents</p>
  <h1>Prime Skill</h1>
  <p class="tagline">Skills tell an agent how to work, MCP servers give it hands, sub-agents give it a team. One vetted representative per capability — no duplicates, every entry licence-checked.</p>
  <div class="stats">
    <span class="stat"><b>{total}</b> skills</span>
    <span class="stat"><b>{len(mcp_servers)}</b> MCP servers</span>
    <span class="stat"><b>{len(subagents)}</b> sub-agents</span>
    <span class="stat"><b>{len(void_entries)}</b> Void entries</span>
    <span class="stat"><b>{len(packs)}</b> packs</span>
    <span class="stat"><b>{special_count}</b> ⭐ specials</span>
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
    print(f"wrote {OUT} ({total} skills, {special_count} specials, {link_only_count} link-only, {len(tag_counts)} tags, {len(mcp_servers)} MCP servers, {len(subagents)} sub-agents, {len(void_entries)} Void entries, {len(packs)} packs)")


if __name__ == "__main__":
    main()

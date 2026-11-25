#!/usr/bin/env python3
"""Validate packs.json and regenerate the README table of packs.

Usage:
  python3 tools/build_packs.py           # regenerate the README table
  python3 tools/build_packs.py --check   # exit non-zero if stale/invalid

Stdlib only. Repo root is the parent of this script's directory.
A pack is a curated cross-branch set for one job: references only, no
new entries, no count changes. Every referenced entry must exist in
its branch manifest (skills.json, mcps.json, subagents.json); Void
entries are never packable (they are not adopted). The shelf of packs
is capped at 8, each pack holds 3-12 entries.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "packs.json"
README = ROOT / "README.md"
START = "<!-- GENERATED:PACKS:START -->"
END = "<!-- GENERATED:PACKS:END -->"
CAP = 8
MIN_ENTRIES = 3
MAX_ENTRIES = 12
REQUIRED = ["name", "title", "description", "why", "added", "entries"]
BRANCH_MANIFESTS = {
    "skills": ("skills.json", "skills"),
    "mcp": ("mcps.json", "servers"),
    "subagents": ("subagents.json", "agents"),
}
BRANCH_LABELS = {"skills": "Skills", "mcp": "MCP", "subagents": "Sub-agents"}


def esc(text):
    return str(text).replace("|", "\\|")


def load(errors):
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"packs.json: unreadable: {exc}")
        return None, []
    packs = data.get("packs")
    if not isinstance(packs, list):
        errors.append("packs.json: 'packs' must be a list")
        return data, []
    return data, packs


def branch_names(errors):
    names = {}
    for branch, (fname, key) in BRANCH_MANIFESTS.items():
        path = ROOT / fname
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            names[branch] = {e.get("name") for e in data.get(key) or []}
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{fname}: unreadable: {exc}")
            names[branch] = set()
    return names


def validate(data, packs, errors):
    if data is not None and data.get("count") != len(packs):
        errors.append(f"packs.json: count {data.get('count')} != {len(packs)} pack(s)")
    if len(packs) > CAP:
        errors.append(f"packs.json: {len(packs)} packs exceeds the hard cap of {CAP}")
    known = branch_names(errors)
    seen = set()
    for pack in packs:
        name = pack.get("name") or "?"
        label = f"packs.json:{name}"
        for field in REQUIRED:
            if field not in pack:
                errors.append(f"{label}: missing field '{field}'")
        if name in seen:
            errors.append(f"{label}: duplicate pack name")
        seen.add(name)
        for field in ("description", "why"):
            if not (pack.get(field) or "").strip():
                errors.append(f"{label}: '{field}' is empty")
        entries = pack.get("entries")
        if not isinstance(entries, list) or not (MIN_ENTRIES <= len(entries) <= MAX_ENTRIES):
            errors.append(f"{label}: entries must be a list of {MIN_ENTRIES}-{MAX_ENTRIES} references")
            continue
        refs = set()
        for entry in entries:
            branch = entry.get("branch") if isinstance(entry, dict) else None
            ref = entry.get("name") if isinstance(entry, dict) else None
            if branch not in BRANCH_MANIFESTS:
                errors.append(f"{label}: entry branch must be one of {sorted(BRANCH_MANIFESTS)}")
                continue
            if (branch, ref) in refs:
                errors.append(f"{label}: duplicate reference {branch}:{ref}")
            refs.add((branch, ref))
            if ref not in known[branch]:
                errors.append(f"{label}: {branch} entry '{ref}' does not exist in its manifest")


def entries_cell(pack):
    groups = []
    for branch in ("skills", "mcp", "subagents"):
        names = [e["name"] for e in pack["entries"] if e["branch"] == branch]
        if names:
            groups.append(f"{BRANCH_LABELS[branch]}: {', '.join(names)}")
    return " · ".join(groups)


def render_readme(packs):
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit("README.md is missing the GENERATED:PACKS markers")
    lines = ["| Pack | What it's for | Why this set | Entries |",
             "|---|---|---|---|"]
    for pack in sorted(packs, key=lambda p: p["name"]):
        lines.append(f"| {esc(pack['title'])} | {esc(pack['description'])} "
                     f"| {esc(pack['why'])} | {esc(entries_cell(pack))} |")
    head, _, rest = readme.partition(START)
    _, _, tail = rest.partition(END)
    return f"{head}{START}\n" + "\n".join(lines) + f"\n{END}{tail}"


def main():
    check = "--check" in sys.argv
    errors = []
    data, packs = load(errors)
    if data is not None:
        validate(data, packs, errors)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        print(f"{len(errors)} validation error(s)")
        return 1
    content = render_readme(packs)
    current = README.read_text(encoding="utf-8")
    if current != content:
        if check:
            print("STALE generated files: README.md (packs table)")
            return 1
        README.write_text(content, encoding="utf-8")
    action = "check OK" if check else "regenerated"
    print(f"{action}: {len(packs)} pack(s), files: README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

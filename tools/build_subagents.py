#!/usr/bin/env python3
"""Validate subagents.json and regenerate the README table of sub-agents.

Usage:
  python3 tools/build_subagents.py           # regenerate the README table
  python3 tools/build_subagents.py --check   # exit non-zero if stale/invalid

Stdlib only. Repo root is the parent of this script's directory.
The shelf is deliberately small: a hard cap of 12 entries, metadata and
links only (no vendored files), and every entry must carry an `access`
line stating plainly what tools and permissions the agent expects.
An entry is a delegable agent definition (its own context, role and
deliverables) or one curated collection of them — never a procedure,
which belongs in the skills.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "subagents.json"
README = ROOT / "README.md"
START = "<!-- GENERATED:SUBAGENTS:START -->"
END = "<!-- GENERATED:SUBAGENTS:END -->"
CAP = 12
REQUIRED = ["name", "title", "kind", "description", "why", "source", "license",
            "stars_at_import", "added", "harnesses", "access", "paid"]
SOURCE_FIELDS = ["repo", "url", "commit"]
KINDS = {"agent", "collection"}


def esc(text):
    return str(text).replace("|", "\\|")


def load(errors):
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"subagents.json: unreadable: {exc}")
        return None, []
    agents = data.get("agents")
    if not isinstance(agents, list):
        errors.append("subagents.json: 'agents' must be a list")
        return data, []
    return data, agents


def validate(data, agents, errors):
    if data is not None and data.get("count") != len(agents):
        errors.append(f"subagents.json: count {data.get('count')} != {len(agents)} agent(s)")
    if len(agents) > CAP:
        errors.append(f"subagents.json: {len(agents)} agents exceeds the hard cap of {CAP}")
    seen = set()
    for agent in agents:
        name = agent.get("name") or "?"
        label = f"subagents.json:{name}"
        for field in REQUIRED:
            if field not in agent:
                errors.append(f"{label}: missing field '{field}'")
        if name in seen:
            errors.append(f"{label}: duplicate agent name")
        seen.add(name)
        if agent.get("kind") not in KINDS:
            errors.append(f"{label}: kind must be one of {sorted(KINDS)}")
        source = agent.get("source") or {}
        for field in SOURCE_FIELDS:
            if not source.get(field):
                errors.append(f"{label}: source.{field} is empty")
        for field in ("description", "why", "access"):
            if not (agent.get(field) or "").strip():
                errors.append(f"{label}: '{field}' is empty (access is the required "
                              "tools/permissions disclosure)")
        harnesses = agent.get("harnesses")
        if (not isinstance(harnesses, list) or not harnesses
                or not all(isinstance(h, str) and h.strip() for h in harnesses)):
            errors.append(f"{label}: harnesses must be a non-empty list of harness names")
        paid = agent.get("paid")
        if paid is not False and not (isinstance(paid, str) and paid.strip()):
            errors.append(f"{label}: paid must be false or a short label (e.g. 'Paid API')")
        if not isinstance(agent.get("stars_at_import"), int):
            errors.append(f"{label}: stars_at_import must be an integer")


def agent_row(agent):
    source = agent["source"]
    commit = source["commit"][:7]
    paid = "" if agent.get("paid") is False else f" · {agent['paid']}"
    stars = f"{agent['stars_at_import']:,}"
    return (f"| [{agent['name']}]({source['url']}) | {esc(agent['kind'])} "
            f"| {esc(agent['description'])} | {esc(agent['why'])} "
            f"| {esc(', '.join(agent['harnesses']))}{paid} "
            f"| {esc(agent['access'])} "
            f"| [{source['repo']}]({source['url']}) @ {commit} · {esc(agent['license'])} · ★ {stars} |")


def render_readme(agents):
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit("README.md is missing the GENERATED:SUBAGENTS markers")
    lines = ["| Sub-agent | Kind | What it is | Why it's here | Harnesses | Tools / permissions it expects | Source |",
             "|---|---|---|---|---|---|---|"]
    for agent in sorted(agents, key=lambda a: a["name"]):
        lines.append(agent_row(agent))
    head, _, rest = readme.partition(START)
    _, _, tail = rest.partition(END)
    return f"{head}{START}\n" + "\n".join(lines) + f"\n{END}{tail}"


def main():
    check = "--check" in sys.argv
    errors = []
    data, agents = load(errors)
    if data is not None:
        validate(data, agents, errors)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        print(f"{len(errors)} validation error(s)")
        return 1
    content = render_readme(agents)
    current = README.read_text(encoding="utf-8")
    if current != content:
        if check:
            print("STALE generated files: README.md (sub-agents table)")
            return 1
        README.write_text(content, encoding="utf-8")
    action = "check OK" if check else "regenerated"
    print(f"{action}: {len(agents)} sub-agent(s), files: README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

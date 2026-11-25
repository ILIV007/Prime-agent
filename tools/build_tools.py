#!/usr/bin/env python3
"""Validate tools.json and regenerate the README table of tools.

Usage:
  python3 tools/build_tools.py           # regenerate the README table
  python3 tools/build_tools.py --check   # exit non-zero if stale/invalid

Stdlib only. Repo root is the parent of this script's directory.
The shelf is deliberately small: a hard cap of 12 entries, metadata and
links only (no vendored files), and every entry must carry an `access`
line stating plainly what the tool runs, reaches, or costs. A tool is a
standalone utility an agent (or its human) uses directly — not a
procedure (a skill), not a protocol server (MCP), not a delegable
worker (a sub-agent), and not a platform deliberately not adopted
(Void).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools.json"
README = ROOT / "README.md"
START = "<!-- GENERATED:TOOLS:START -->"
END = "<!-- GENERATED:TOOLS:END -->"
CAP = 12
REQUIRED = ["name", "title", "kind", "description", "why", "source", "license",
            "stars_at_import", "added", "access", "paid"]
SOURCE_FIELDS = ["repo", "url", "commit"]
KINDS = {"cli", "web", "app", "api", "dataset", "library"}


def esc(text):
    return str(text).replace("|", "\\|")


def load(errors):
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"tools.json: unreadable: {exc}")
        return None, []
    tools = data.get("tools")
    if not isinstance(tools, list):
        errors.append("tools.json: 'tools' must be a list")
        return data, []
    return data, tools


def validate(data, tools, errors):
    if data is not None and data.get("count") != len(tools):
        errors.append(f"tools.json: count {data.get('count')} != {len(tools)} tool(s)")
    if len(tools) > CAP:
        errors.append(f"tools.json: {len(tools)} tools exceeds the hard cap of {CAP}")
    seen = set()
    for tool in tools:
        name = tool.get("name") or "?"
        label = f"tools.json:{name}"
        for field in REQUIRED:
            if field not in tool:
                errors.append(f"{label}: missing field '{field}'")
        if name in seen:
            errors.append(f"{label}: duplicate tool name")
        seen.add(name)
        if tool.get("kind") not in KINDS:
            errors.append(f"{label}: kind must be one of {sorted(KINDS)}")
        source = tool.get("source") or {}
        for field in SOURCE_FIELDS:
            if not source.get(field):
                errors.append(f"{label}: source.{field} is empty")
        for field in ("description", "why", "access"):
            if not (tool.get(field) or "").strip():
                errors.append(f"{label}: '{field}' is empty (access is the required "
                              "runs/reaches/costs disclosure)")
        paid = tool.get("paid")
        if paid is not False and not (isinstance(paid, str) and paid.strip()):
            errors.append(f"{label}: paid must be false or a short label (e.g. 'Paid API')")
        if not isinstance(tool.get("stars_at_import"), int):
            errors.append(f"{label}: stars_at_import must be an integer")


def tool_row(tool):
    source = tool["source"]
    commit = source["commit"][:7]
    paid = "" if tool.get("paid") is False else f" · {tool['paid']}"
    stars = f"{tool['stars_at_import']:,}"
    return (f"| [{tool['name']}]({source['url']}) | {esc(tool['kind'])}{paid} "
            f"| {esc(tool['description'])} | {esc(tool['why'])} "
            f"| {esc(tool['access'])} "
            f"| [{source['repo']}]({source['url']}) @ {commit} · {esc(tool['license'])} · ★ {stars} |")


def render_readme(tools):
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit("README.md is missing the GENERATED:TOOLS markers")
    lines = ["| Tool | Kind | What it does | Why it's here | What it runs / costs | Source |",
             "|---|---|---|---|---|---|"]
    for tool in sorted(tools, key=lambda t: t["name"]):
        lines.append(tool_row(tool))
    head, _, rest = readme.partition(START)
    _, _, tail = rest.partition(END)
    return f"{head}{START}\n" + "\n".join(lines) + f"\n{END}{tail}"


def main():
    check = "--check" in sys.argv
    errors = []
    data, tools = load(errors)
    if data is not None:
        validate(data, tools, errors)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        print(f"{len(errors)} validation error(s)")
        return 1
    content = render_readme(tools)
    current = README.read_text(encoding="utf-8")
    if current != content:
        if check:
            print("STALE generated files: README.md (tools table)")
            return 1
        README.write_text(content, encoding="utf-8")
    action = "check OK" if check else "regenerated"
    print(f"{action}: {len(tools)} tool(s), files: README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

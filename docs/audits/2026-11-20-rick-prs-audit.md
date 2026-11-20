# Audit: Rick's PRs #2–#8 (2026-11-20)

- **Auditor:** Agent: Nova
- **Date:** 2026-11-20
- **Scope:** PRs #2–#8 (merged 2026-11-18, except #8 on 2026-11-20), audited at head `8f5cc6b` (which adds the 2026-11-20 batch: SkillEvaluator, univer-integrate, 2× Clayzo link-only — those four are NOT part of this audit).
- **Order:** owner asked for a checkup of Rick's work, fix clear-cut issues, update/tidy up, and sign the work like Rick does.

## Owner decisions recorded during this audit

1. **No count limits.** The owner (2026-11-20 ~18:47): "حد نمیخواد بزاری برای تعداد ها" — no limits on numbers/counts. Consequence: the development ~32 split tripwire is OFF as a cap; development at 38 does NOT trigger a split, and no split is proposed on numbers alone. The research ~6 general-research tripwire is likewise off (general research is at 6 — see open items). The MCP shelf's hard cap of 12 is a separate design decision and stays untouched.
2. **BugHunter Void: NO.** The owner: "باگ هانتر هم وید نباشه چیز اصلیه!" — BugHunter is main-collection material, not Void. The 12 FULL skills in Security stand as-is. No Void entry is added, and none should be added later without a new owner call.

## What was checked

- `git pull` (clean, head `8f5cc6b`); all three validators `--check`: `build_index` OK (125 skills), `build_void` OK (14 entries), `build_mcps` OK (6 servers).
- Counts verified against the manifests: 125 skills — development 38, design 22, research 19, security 19, marketing 13, media 11, reverse-engineering 2, cookbook 1; link-only 8; specials 8; Void 14; MCPs 6.
- Every one of the 30 added skill folders: `SKILL.md` present with valid YAML frontmatter (`name` + `description`), `skill.json` present, `LICENSE` present; all 12 BugHunter folders also carry `LICENSE-CONTENT`. Tags checked against the 16-tag controlled vocabulary — all in-vocab, 1–3 per entry.
- Licenses re-verified against the GitHub API (live values on 2026-11-20): ECC 307,614★ MIT; BugHunter 13,358★ at vetting, dual MIT + CC BY 4.0; GSAP 18,815★ MIT; humanizer 71,562★ MIT; paperclip 115,376★ MIT; craft-anything 39,237★, dual MIT OR Apache-2.0.
- Dedupe reviewed per addition (see verdicts). README "At a glance" line reads `125 skills · 8 categories · 8 link-only` — current. `site/index.html` regenerated with `tools/build_site.py` — byte-identical to the committed copy, so the committed site is fresh.
- CI on head `8f5cc6b`: validate ✅ success, pages ✅ success. Live site (https://iliv007.github.io/prime-skill/) fetched 2026-11-20 and renders the new entries (agent-architecture-audit, canary-watch, cost-aware-llm-pipeline, eval-harness, prompt-caching-strategy, skillevaluator, univer-integrate all visible).

## Per-PR verdicts

| PR | Change | Verdict |
|---|---|---|
| #2 (2026-11-18 11:55) | Cookbook section + `telegram-bot-workers` (in-house skill, source = this repo) | **OK.** Scope line exists in `build_index.py` SCOPES and in `categories/cookbook/README.md`. One open item: the category has 1 entry, below the design doc's "at least 2 entries" guideline — no forced action per the owner's no-count-limits decision (see open items). |
| #3 (2026-11-18 22:26) | 12 Claude-BugHunter skills FULL into Security (92 → 104): bb-methodology, bug-bounty, evidence-hygiene, hunt-api-misconfig, hunt-auth-bypass, hunt-idor, hunt-llm-ai, hunt-rag-vector, hunt-ssrf, recon-scope-triage, report-writing, triage-validation @ `b63ae349` | **OK.** All real SKILL.md files, dual license recorded as `MIT + CC BY 4.0` with both license files vendored per folder. The 12 are the distinctive singles (orchestrators + workflow + the most reusable hunts); the remaining ~71 stay out deliberately. Partial overlaps with `api-security` / `security-review` are angle differences (offensive patterns from disclosed reports vs defensive checklists), not duplicates. Per the owner's decision above, no Void bundle entry is added. |
| #4 (2026-11-18 22:29) | Paperclip → Void (12 → 13) | **OK.** Honest `why_valuable` (agent-orchestration platform, budget-governance reference) + `why_not_included` (a platform, not a skill; always-on multi-CLI model vs the owner's credit budget). No main-collection duplicate. |
| #5 (2026-11-18 22:42) | 8 official GSAP skills → Design (104 → 112), from greensock/gsap-skills, MIT | **OK.** Vendor's own correct-usage layer for the GSAP engine. No conflict with `emil-design-eng` (motion-craft judgment, no engine) or `algorithmic-art` (generative art coding). Note: the upstream repo's last push was 2026-07-29 — quiet, but official and complete; no action. |
| #6 (2026-11-18 22:50) | 8 cherry-picked ECC skills (112 → 120), from affaan-m/ECC — 5 to development (agent-architecture-audit, canary-watch, cost-aware-llm-pipeline, eval-harness, prompt-caching-strategy), 2 to research (scientific-db-openalex-database, scientific-thinking-scholar-evaluation), 1 to security (agent-security-hardening) | **OK.** ECC = affaan-m/ECC, "The agent harness performance optimization system" (307k★). Each entry has a distinct job with a stated gap in its `why`. Genuine adjacencies, not duplicates: `eval-harness` (eval methodology for agent behaviour) vs `skillevaluator` (quality scoring of SKILL.md files); `agent-architecture-audit` (12-layer diagnosis of a misbehaving agent product) vs `improve` (audit-first advisor producing implementation plans for a codebase); `cost-aware-llm-pipeline` (routing + budget tracking) vs `prompt-caching-strategy` (cache-oriented prompt structure); `agent-security-hardening` is the defensive counterpart the security shelf was missing. One minor open item: `eval-harness` / `canary-watch` contain Claude-Code-specific paths (`.claude/evals/`, `~/.claude/canary-watch.log`) vendored as-is with `adapted: false` — the manifest description discloses the framing, so this is a tidy-up candidate, not a defect (see open items). |
| #7 (2026-11-18 22:54) | Humanizer → Marketing (120 → 121), from blader/humanizer, MIT | **OK.** Removes AI tells from prose; distinct from `copy-editing` (sharpens marketing copy). |
| #8 (2026-11-20 14:34) | Craft Anything → Void (13 → 14) | **OK.** Honest `why_valuable` (automated study/build/verify rebuild loop, no equivalent in the collection) + `why_not_included` (a Rust platform with zero SKILL.md files; three weeks old, early alpha, hype-velocity stars — all stated plainly). No main-collection duplicate; neighbours REA's territory from a different class, as the entry itself says. |

## Fixes made

**None.** Two candidate issues were examined and deliberately left alone:

1. `telegram-bot-workers` records `source.commit: 0ea9096`, a commit that does not contain the `categories/cookbook` tree (it first appears in `b70b9da`). This looks like a provenance error, but it is Rick's **documented convention**, stated in the skill's own `adaptations` field: "source.commit records main's HEAD at authoring time; the skill's own history is this repo's history." Changing it to `b70b9da` would contradict the field's own note. If the owner wants `source.commit` to mean "first commit containing the skill" instead, the fix is a one-line change (`0ea9096` → `b70b9da`) plus regeneration — flagged as an open question, not applied unilaterally.
2. The `.claude/` path references in `eval-harness` / `canary-watch` (see #6 above) were not edited: the description already discloses the framing, and editing upstream skill content is an adaptation decision, not a clear-cut fix. Suggested tidy-up is listed under open items.

## Totals after the audit (verified, unchanged by this audit)

125 skills (development 38, design 22, research 19, security 19, marketing 13, media 11, reverse-engineering 2, cookbook 1) · 8 link-only · 8 ⭐ specials · Void 14 · MCPs 6/12.

## Open items

- **Cookbook has 1 entry** (below the design doc's ≥2 guideline for a new category). No forced action per the owner's no-count-limits decision. It grows when a second in-house recipe exists; the alternative — folding `telegram-bot-workers` into development until then — needs the owner's call.
- **`source.commit` convention for in-house skills** (see "Fixes made" §1): HEAD-at-authoring-time (`0ea9096`) vs first-commit-containing-the-skill (`b70b9da`). Owner's call if he wants it changed.
- **Harness-neutral tidy-up (optional):** generalise the `.claude/evals/` paths in `eval-harness` (4 spots) and the `~/.claude/canary-watch.log` path in `canary-watch`, declare `adapted: true` with an `adaptations` note. Small, safe, but an upstream-content edit — needs a go-ahead, not assumed.
- **Research general-research at 6** (deep-research, exa-search, agent-reach, literature-review, scientific-db-openalex-database, scientific-thinking-scholar-evaluation). The design doc's split tripwire for research is count-based and therefore off per the owner's decision — recorded here only so the count is visible, no split proposed.
- **Nit, not Rick's:** `skillevaluator`'s `why` says "121-skill collection" — true at its import (2026-11-20 batch, 121 → 125), now a snapshot like `stars_at_import`. Leave or reword on a later pass; not touched in this audit.
- **GSAP upstream quiet since 2026-07-29** (official vendor repo, complete set of 8 skills). No action; revisit only if GSAP ships a new major version.

## Signature convention (shared with Rick)

Rick signs his PR bodies with a trailing `Agent: Rick` line and records authorship in the cookbook skill's `adaptations` field. This audit note and its commit are signed the same way, as `Agent: Nova`.

Agent: Nova

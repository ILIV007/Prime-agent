# Rich Messages — field reference

Rich Messages (Bot API 10.x) render structured content natively in every
Telegram client: headings, tables, math, highlighted code, collapsible
sections. They are the right tool for dashboards, reports, guides and
anything the user reads once — and the wrong tool for anything the bot
must later change.

## Sending

`sendRichMessage` with a `rich_message` object. The practical input is an
HTML-flavoured payload (markdown converters exist in the Python world;
on Workers you assemble the HTML/entities yourself):

```json
POST https://api.telegram.org/bot<TOKEN>/sendRichMessage
{
  "chat_id": 123456789,
  "rich_message": { "html": "<h3>Status</h3><table>…</table>" }
}
```

## Element catalog

| Element | Syntax / tag | Good for |
|---|---|---|
| Headings | `#` … `####` or `<h1>`–`<h4>` | Sectioned reports, guides |
| Table | markdown table or `<table><tr><th>…` | Status, comparisons, stats |
| Math | `$…$` → `<tg-math>`, `$$…$$` → `<tg-math-block>` | Formulas |
| Code block | fenced block with language tag | Highlighted code (python, javascript, typescript, sql, bash, json, yaml, go, rust, …) |
| Inline code | backticks | Commands, ids, values |
| Lists | `-` / `1.` with nesting | Steps, inventories |
| Styles | `**bold**`, `*italic*`, `~~strike~~` | Emphasis |
| Spoiler | `\|\|hidden\|\|` | Answers, secrets, reveals |
| Block quote | `>` | Quotations, summaries |
| Divider | `---` | Section breaks |
| Collapsible | `<details><summary>…</summary>…</details>` (raw HTML only) | Logs, changelogs, verbose detail |
| Expandable quote | `<blockquote expandable>` (raw HTML only) | Long text behind "show more" |
| Sub/superscript | `<sub>`, `<sup>` (raw HTML only) | H₂O, x² |

Converters escape raw-HTML-only tags (`details`, `sub`, `sup`) instead of
emitting them — if you rely on those, build the HTML yourself.

## The no-edit rule (hard constraint)

**There is no `editMessageRichText`. It returns 404.** A rich message is
fire-and-forget: once sent it cannot be edited, restyled or appended to.

Consequences for design:

- Menus, wizards, progress indicators, live dashboards — anything that
  updates in place — must be **regular entity-based messages** edited
  with `editMessageText`. Never rich.
- A callback flow that "refreshes" rich content must send a **new** rich
  message (and optionally delete the old one). Design for that: rich
  content should be a deliverable, not a surface.
- Streaming (`sendMessageDraft`) applies to regular messages; a rich
  result lands as one final message.

## When to go rich — the AUTO heuristic

From the fleet's admin/publisher bot, where AUTO is the default:

1. The source content is already rich (it arrived structured), or
2. the content would otherwise split into multiple messages, or
3. it contains a real table or comparable structure.

Otherwise a well-built entity message is lighter, editable, and safer.
Walls of plain text are still wrong when a table would do — but so is a
rich message the bot can never fix.

## Gotchas

- Log every failed `sendRichMessage` with the API description; rich
  payloads fail on malformed nesting more often than plain text fails.
- LaTeX backslashes: in languages with escape-heavy string literals,
  double them (`\\frac`) or use raw strings.
- Test rendering in a real client per platform you care about; block
  support is client-dependent and degrades silently.
- Rich formatting does not exempt you from length discipline — keep
  deliverables scannable, and push overflow into `<details>`.

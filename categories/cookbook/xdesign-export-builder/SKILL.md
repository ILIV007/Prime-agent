---
name: xdesign-export-builder
description: >
  Build a working Telegram bot from an xDesign export zip: read spec.json
  as the source of truth, turn its steps into a state machine, and
  implement it on Cloudflare Workers or any webhook bot stack. Use when
  you have an export zip and need the bot it describes, built faithfully
  and without guessing.
license: MIT
---

# xDesign Export Builder

An xDesign export is a bot design frozen into files: every screen, button,
question, branch, payment and wait, already decided by a designer. Your job
is implementation, not design. The export tells you exactly what to build —
read it, don't re-decide it.

## When to use — and when not to

Use this skill when you have an export zip (`.xdesign.zip`) and are asked to
build the bot it describes.

Do **not** start building when:

- There is no export yet — designing belongs in the editor, not in code.
  Ask for the zip.
- The export's checks list has **errors**. Errors mean the design asks
  Telegram to do something it cannot do. Send them back to the designer;
  never "fix" an error by changing the design yourself.
- A step is ambiguous and neither `design.md` nor the spec resolves it.
  Ask the designer; a guess here ships as a wrong bot.

## The export zip

Unzip it and confirm these files are present:

| File | What it is |
| --- | --- |
| `spec.json` | The source of truth. Machine-readable, format `xdesign.bot-spec`, version 1. When anything disagrees, this file wins. |
| `design.md` | The human-readable map: sections, steps, the flow diagram, every text and button, variables, and the checks. Read this first to understand the bot, then build from `spec.json`. |
| `HOW-TO-READ.md` | The tool's own builder guide for this export. Read it alongside this skill; it documents the same format from the tool's side. |
| `bot-spec.schema.json` | The JSON Schema `spec.json` validates against. Use it to validate the file before you trust it. |
| `media/` | Every uploaded file, named `<id>.<ext>`. Upload each once to Telegram, keep the returned `file_id`, and reuse it — never re-upload per user. |
| `pictures/` | Rendered previews per step and language, plus bot-profile, empty-chat and commands-menu shots. Reference images for what the screens should look like; not assets to send. |

Check `format` is `xdesign.bot-spec` and `formatVersion` is `1` before doing
anything else. A different version means this skill's mapping may not apply —
stop and say so.

## Reading `spec.json`

Top-level sections, in the order you will use them:

- **`design`** — the design's id, name and document version. Record the
  version in your code or README; a later export is a new version, not an
  edit.
- **`telegram`** — the Bot API version the design targets, and the chat scope
  (`private`: this format only describes one-to-one bots).
- **`languages`** — `default`, the full list `all`, and `rightToLeft`.
  Every user-facing string is a per-language map; a missing language falls
  back to `default`. Never fall back to another language, and never show a
  raw language code to a user.
- **`bot`** — profile: name, about and description per language, photo,
  menu button mode, and the `commands` list (each with its start point).
  Register all of these with BotFather / `setMyCommands` per language.
- **`startPoints`** — the entries into the flow. A start point fires on a
  command, a `/start` deep link (with an optional payload match and a place
  to save the rest of the payload), a payment completing, a refund, a
  subscription changing, a user blocking or restarting the bot, an unmatched
  message (fallback), or a scheduled broadcast (with its audience and
  timing). Build one entry handler per trigger type, not one handler per
  start point.
- **`steps`** — the flow itself. See below.
- **`parts`** — reusable pieces: button-row sets and text fragments that
  steps reference by id. Expand them where they are used; keep one copy of
  the definition.
- **`variables`** — every variable with its type (`text`, `number`, `yesNo`,
  `phone`, `location`, `file`, `users`, `chat`, `poll`), where it is set,
  and a test value. Test values belong to the editor's simulator — in
  production a variable starts unset unless a step sets it.
- **`testSwitches`** — yes/no or multi-choice toggles the designer flips
  while simulating. They are design-time only: never expose them to real
  users, and never ship a test value as a default.
- **`media`** — the uploaded files with kind, mime, size and dimensions.
- **`checks`** — the issues found at export time. See the Checks section.
- **`notes` / `sections`** — designer notes and the map's visual grouping.
  Useful for understanding intent; they change nothing at runtime.
- **`cameFrom`** on steps and start points — which steps link here. Use it
  to build the `back` history, not to guess the flow.

## The ten step kinds

Every step has a stable `id` — a short lowercase name with underscores.
Use ids **verbatim** as callback data, state names and variable keys. Never
rename them: the designer, the checks and any future export all refer to
the same ids. A target of `null` means no outgoing arrow — treat it as the
flow ending there unless the design says otherwise.

| Kind | What it means in code |
| --- | --- |
| `message` | Send (or show) a message with optional keyboard and options, then follow `next`. `onStop` is where to go if the user stops a streamed draft. |
| `question` | Ask for input and wait. `expects` says the kind (`text`, `number`, `email`, `phone`, `location`, `photo`, `video`, `file`, `voice`, `audio`, `any`). `checks` give the validation rules (length, range, whole-number, pattern, file size/types). Validate, save to `saveTo`, and follow `next`. On invalid input, send `wrongAnswer.message`; after `maxTries`, follow `afterMaxTries`. `cancel` lists the words that abort the question and where they lead. |
| `if` | Branch. `cases` are checked in order; each has a condition, a short text to show, and a target. `otherwise` is the fall-through. Evaluate in order, first match wins. |
| `remember` | Change variables without showing anything: set, clear, add, subtract, append. Then follow `next`. |
| `wait` | Pause the flow for `amount` + `unit` (seconds to days). `ifUserActs` says whether user input cancels the wait or is held; `stopWhen` is a condition that can end it early. The wait must survive a restart — see State below. |
| `devStep` | A human job, not bot behaviour. Stop the flow here and surface the job: what it `uses` (inputs), what it `sets` (expected outputs), and its labelled `outcomes`. When a human reports an outcome, resume at that outcome's target. Never auto-pick an outcome. |
| `goTo` | An unconditional jump to `target`. |
| `end` | The flow ends. Clear the per-user session (keep the variables the design says to keep, if any). |
| `invoice` | A payment step. See Payments below. |
| `action` | A one-shot Telegram action with no message of its own: react to a message, pin/unpin, delete, send a gift, send a chat action (typing, uploading…), or refund a payment. Then follow `next`. |

Conditions (in `if` cases, `wait.stopWhen`, and elsewhere) test a variable
(set/empty/equals/not-equals/contains/starts-with/greater/less), a test
switch, the user's language, or channel membership. A condition's `value`
may itself be another variable — resolve it before comparing.

## Buttons and keyboards

A button has an `id`, a per-language `label`, a `look` (`default`,
`primary`, `success`, `danger` — one primary action per screen), an
optional custom-emoji icon with a plain-text fallback, and a `does`:

- `goTo` — jump to a target (or `stay`), and `show` says how: `edit`
  (edit the current message in place — the default for menus), `new`
  (send a fresh message), or `replace`. It may also pop a `toast` (short
  hint) or an `alert` (blocking dialog), and may run `remember` actions
  first.
- `url`, `loginUrl`, `copyText` — open a link, log in via Telegram Login,
  or copy text to the clipboard. These need no target.
- `pay` — pay the invoice of the current step.
- `text` — send a text reply as if the user typed it, then go to a target.
- `sharePhone` / `shareLocation` — request contact or location, save it,
  then go to a target.

Keyboards are `inline` or `reply` (rows of buttons, or a reference to a
reusable `parts` row set). Reply keyboards may be one-time; inline keyboards
may keep the reply field open. Callback data is capped at **64 bytes** —
the step and button ids are designed to fit; do not add prefixes or payloads
that push them over. Keep all localized text in the label, never in the
callback data.

## Texts, entities and languages

Each text is a per-language map. Every language entry carries the plain
`text`, an `entities` array (bold, italic, underline, strikethrough,
spoiler, code, pre, blockquote, expandable quote, links, custom emoji,
dates — offsets and lengths in **UTF-16 code units**), a ready-made HTML
rendering, and the `variables` placeholders (`{variable_id}`) with their
offsets.

Rules:

- Render with **entities, not `parse_mode`**. Build `{text, entities}`
  from the spec and substitute variables first, then re-compute entity
  offsets — never search for a needle in the localized string afterwards.
- For long AI-style output the design may use drafts: send a draft first,
  then finalise. The draft's stop button ends generation and follows the
  step's `onStop`.
- Rich (structured) content — headings, tables, code blocks, quotes,
  lists — is a document in the spec, not a flat string. If your stack
  supports rich messages, map the document blocks to them; rich messages
  **cannot be edited**, so anything interactive stays entity-based.
- RTL languages: direction is per string. Keep callback data ASCII and
  expect mixed-direction strings (Persian text with English terms and
  numbers); use direction marks (U+200F/U+200E) around embedded LTR runs
  when a client renders them scrambled.

## The Checks — read before you build

`checks` is an array of issues, each with a `level` (`error`, `warning`,
`info`), a `code`, a location (`where`, plus `button` and `language` when
relevant), a plain-language `message`, and `ignored` (whether the designer
marked it ignored).

- **Errors block the build.** They mean the design asks for something
  Telegram cannot do. Do not build around them.
- **Warnings are must-fix by default.** The designer can mark one ignored
  in the tool; an ignored warning in the export is a deliberate decision —
  respect it, but note it in your handover.
- **Info is advisory** — worth reading, safe to ship past.

The checks cover, roughly: text lengths and missing translations; keyboard
and button rules (counts, sizes, callback data, custom emoji); media and
content references; payment setup; event triggers; flow shape (unreachable
steps, dead ends, missing targets); language coverage; variables that are
used but never set (or set but never used); and bot setup (profile,
commands). You do not need to re-implement these rules — the export already
ran them. Your job is to read the list and act on it.

## The state machine

One record per user, keyed by chat id. It holds: the current step id, all
variables, a history stack (for `back` targets), the pending question
(step, tries used, expected kind), and any active wait (deadline + the step
to resume at).

- **Persistence is not optional.** State must survive restarts and deploys:
  a store with strong reads (KV with a merged user record, D1, or any
  database your stack has). Never keep the only copy in process memory.
- **Back:** a `back` target means the message step the user came from —
  pop the history stack. A step with no history behind it has nowhere to
  go back to; treat that as a design error and say so.
- **Waits:** store the deadline, not a timer. On every wake-up (any update,
  or a scheduled tick), check expired waits and resume them. A wait that
  only lives in a `setTimeout` dies with the process.
- **Questions:** an answer that arrives while no question is pending is
  not an answer — route it to the fallback start point.
- **Retries and duplicates:** Telegram redelivers updates. Dedupe on
  `update_id` and answer every callback query first, before any other
  work — a spinning button reads as a dead bot.
- **Editing:** menus edit the current message in place. Know what Telegram
  cannot edit: a message's media type cannot change via edit, very old
  messages cannot be edited, and rich messages cannot be edited at all.
  When an edit is impossible, send a new message and retire the old one —
  never leave two live menus for the same flow.

## Payments

An `invoice` step carries title, description, photo, currency, `prices`
(label + amount per line), `payload`, and optionally a `subscription`
(period in days) or physical-goods fields (name/phone/email/address,
shipping options). `checkout` may hold a refusal message.

- Create the invoice with the payload from the spec — the payload is how
  you recognise the payment later; never invent your own.
- Answer `pre_checkout_query` (approve or refuse with the spec's text),
  then handle `successful_payment` and follow `next`.
- Refunds are an `action` step; subscription changes and refunds are also
  start-point triggers, so build those handlers.
- Test every invoice in test mode with test Stars/cards before shipping.
  A payment flow you have not watched succeed end to end is not done.

## Implementation paths

**Cloudflare Workers (recommended for this fleet).** Follow the
`telegram-bot-workers` skill: webhook with a `secret_token` verified on
every POST, answer 200 immediately and do the work in `waitUntil`, entity
formatting, the 4096-unit split, 64-byte callback data, per-user state in
KV (one merged record, TTLs on session keys) or D1/Durable Objects where
strong consistency matters, and its production checklist before shipping.
Waits become a scheduled cron tick that resumes expired waits.

**Any other stack.** The same shape applies: a webhook endpoint (never
long polling in production), a Bot API client, a per-user state store, and
a step runner that dispatches on `kind`. The spec is stack-agnostic — only
the transport and storage change.

In both paths: build the step runner as a table keyed by `kind`, one
function per kind, driven entirely by the spec. Hard-coding one design's
flow into `if` chains means the next export starts from zero.

## Validation checklist — before calling the bot done

- [ ] `spec.json` validates against `bot-spec.schema.json`; `formatVersion`
      is 1; every referenced step, part, variable and media id exists.
- [ ] Checks list: zero errors; every warning either fixed or explicitly
      ignored by the designer.
- [ ] Walk every path in the design's own Try-it order, in every shipped
      language, including the fallback language and one RTL language.
- [ ] Every question: valid answer, invalid answer, max tries, cancel
      words, and a wrong-type answer (e.g. text where a number is expected).
- [ ] Every branch: each `if` case and the `otherwise` path, with variables
      set to force each one.
- [ ] Back navigation from every screen that offers it; a wait that fires
      while the process is restarted mid-wait.
- [ ] Every invoice in test mode, plus a refund and a subscription change.
- [ ] Every `devStep`: the job surfaces with its inputs, and each outcome
      resumes at the right step.
- [ ] Commands registered per language; menu button set; profile photo,
      name, about and description match `bot`.
- [ ] One over-limit message sent on purpose (4096+ units) to prove the
      split works; one duplicate update injected to prove dedup works.

## Limits — stated plainly

- The format is **version 1**, from a tool days old with a single
  maintainer. Treat `spec.json` as the contract, not the tool's
  documentation: if a future export changes shape, re-read the schema
  first and say what changed.
- The upstream project currently ships **without a licence file** (its
  README reserves all rights; the author has said MIT is intended but it
  has not landed). This skill contains **no material copied from the tool**
  — its text, mapping and checklist are original work written from the
  format's structure and from public Bot API knowledge. Do not copy the
  tool's guide, docs or code into a skill or a repo; link to them instead.
- This skill builds bots from exports. It does not design them, run the
  editor, or talk to the tool's server. A bad design built faithfully is
  still a bad design — that is the designer's call, not yours.

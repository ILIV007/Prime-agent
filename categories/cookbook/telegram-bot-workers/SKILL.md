---
name: telegram-bot-workers
description: >
  Build production Telegram bots on Cloudflare Workers with the raw Bot API
  (no framework): secure webhooks, entity-based formatting, Rich Messages,
  edit-in-place menus, KV state discipline, and the production invariants
  that keep a bot alive. Use when creating, extending, reviewing or debugging
  a Telegram bot that runs on Workers or another serverless edge runtime,
  especially multilingual or RTL bots and AI-backed bots.
license: MIT
---

# Telegram Bot on Cloudflare Workers

Build the bot the way the fleet runs: one Worker, raw Bot API over `fetch`,
no framework and no dependencies unless a requirement forces one. Distilled
from production bots (channel AI commenters, admin publishers, market
posters, prompt optimizers) running on the Workers free plan.

## Stack decision

- **Default: raw Bot API + a thin in-repo client.** A bot is HTTP calls and
  JSON. A framework earns its place only when you need its session/menu
  machinery across many flows, or Mini App validation at scale — then
  grammY on Workers is the one maintained choice (Telegraf is dormant
  since 2024; most Python bot skills assume a VPS and polling).
- **Runtime shape:** webhook on Workers, never long polling in production.
  Polling is for local debugging only — `getUpdates` and a webhook are
  mutually exclusive and polling burns a always-on process for nothing.

## Webhook contract

- Set the webhook with a `secret_token` and verify the
  `X-Telegram-Bot-Api-Secret-Token` header on **every** POST. No secret,
  no service — anyone who learns the URL can inject fake updates and burn
  your AI quota.
- Set `allowed_updates` as narrow as the bot needs. Every excluded type is
  CPU and invocations you never pay.
- Answer `200` immediately and do the real work in `ctx.waitUntil`.
  Telegram retries slow or failed deliveries, so a handler that awaits a
  20-second AI call inline gets the same update twice and pays twice.
- Dedupe on `update_id` (in-isolate LRU is enough; delivery retries are
  short-lived). Age-gate anything you process late: an update older than a
  few minutes after downtime is a stale command, not work — drop it.
- Never return stack traces or internal errors in the webhook response.

## The Telegram client layer

Write these helpers once; every bot needs them:

- `apiCall(method, body)` — POSTs JSON, throws on `ok: false` with the
  Telegram description and error code. Log failures; never swallow them
  silently.
- **Entity-based formatting, not `parse_mode`.** Build `{text, entities}`
  from segments (`bold`, `italic`, `code`, `pre`, `blockquote`,
  `expandable_blockquote`, `text_link`). This kills MarkdownV2/HTML
  escaping bugs outright and is the only sane option for RTL text.
  Offsets are UTF-16 code units — exactly what JS string `.length` counts.
  Never locate an entity with `indexOf` on a needle that may not exist in
  the localized string: a `-1` result silently shifts the entity onto the
  wrong characters (this bug shipped once in a Persian footer; compute
  offsets while assembling, never by searching afterwards).
- `splitMessage(text, entities)` — nothing over **4096 UTF-16 units** ever
  reaches `sendMessage`. Split on paragraph/line boundaries, keep entity
  ranges consistent per chunk, never split inside a `pre` block if it can
  be avoided, and leave headroom (4000) instead of slicing at the limit.
- Keyboards: `callback_data` is capped at **64 bytes** — keep it ASCII
  (`cat_code`, `preset_bank_12`), put all localized text in the button
  label, and namespace prefixes per flow. Use button `style`
  (primary/success/danger) semantically: one primary action per screen.
- `copy_text` buttons for anything the user will paste elsewhere.
- Answer every callback query **first**, before any other await —
  Telegram's callback timeout is ~10 seconds and a spinning button reads
  as a dead bot.

## UX patterns that work

- **Edit in place.** One home message per user; navigation edits it
  (`editMessageText`). Sending a fresh message per tap buries the chat.
  Deliverables (results, posts) are new messages; menus are not.
- **Acknowledge instantly.** A reaction (⚡) or a single status message
  beats fake progress animations — no sleep-driven edit loops; they waste
  subrequests and hit rate limits.
- **Stream long AI output** with `sendMessageDraft` in private chats
  where supported, then finalise into a result message. Fall back to one
  status edit, not nine.
- **Rich Messages** (`sendRichMessage`) for genuinely structured,
  fire-and-forget content — tables, headings, collapsible sections,
  highlighted code. Read `references/rich-messages.md` before using them:
  the hard rule is that **rich messages cannot be edited**, so anything
  interactive or updatable stays entity-based. Fleet heuristic (AUTO):
  go rich only when the content is already rich, would otherwise split
  into multiple messages, or contains a real table.
- **RTL:** direction is per-string. Keep `callback_data` ASCII, expect
  mixed-direction strings (Persian text + English terms + numbers) and
  use Unicode direction marks (U+200F/U+200E) around embedded LTR runs
  when a client renders them scrambled. Entity formatting survives RTL
  reordering; Markdown markers often do not.
- **Groups:** privacy mode is on by default — the bot sees commands,
  mentions and replies only. Turning it off applies only after the bot is
  removed and re-added (or promoted to admin). Bots never see other bots
  unless Bot-to-Bot Communication Mode is enabled in BotFather, and then
  loop guards (dedupe, depth caps, rate limits) are your job.

## State and storage discipline (Workers free plan)

- KV is eventually consistent and the free tier allows ~1,000 writes/day.
  Budget writes: one merged user record (`u:<chatId>`), at most ~2 writes
  per user message, TTLs on session/step keys, and never write on every
  message just to "track" a user — track once.
- In-isolate `Map` caches lie across isolates; treat them as hints, never
  as the source of truth for money, counters or coordination. Need strong
  consistency or per-chat ordering? Durable Objects. Relational data? D1.
- Broadcasts: respect ~30 msg/s global and ~1 msg/s per chat, honour
  `parameters.retry_after` on 429, and count subrequests — a free-plan
  invocation caps at 50, so chunk broadcasts across invocations instead
  of looping inside one request until it dies silently.

## AI-backed bots

- One provider interface (`generate({system, user})`), a fallback chain
  behind it, ~20–25s per-attempt timeout, one retry maximum. Verify every
  model in the chain live before shipping it — free-tier model catalogs
  churn monthly and a dead first entry silently taxes every request.
- Per-user rate limit and an input length cap are not optional on a
  public bot; without them one user drains the provider quota.
- Keep prompts out of per-message KV state (store a prompt id, not the
  text) — state stays small and prompts stay versioned in code.

## BotFather and profile

- Register commands with `setMyCommands` per language (default list is
  the fallback; scoped lists replace, never merge). Set name,
  description and short description per language too — empty localized
  variants look broken to exactly the users they serve.
- Set a chat menu button (`setChatMenuButton`) pointing at the bot's home.
- Tokens live in Worker secrets / a vault, never in the repo, chat or
  logs. Rotation: `/revoke` in BotFather, update the one secret,
  redeploy, verify with `getMe` + `getWebhookInfo`.

## Before you ship

Run `references/production-checklist.md` end to end. Then test live:
inject real updates, walk every screen in every shipped language, force
each provider to fail, and send one over-limit message on purpose.

## References

- `references/rich-messages.md` — Rich Message elements, payload shape,
  and the no-edit rule with its workarounds.
- `references/production-checklist.md` — the invariants checklist:
  ingestion, loops, formatting, limits, errors, recovery.
- Official docs: Telegram Bot API (https://core.telegram.org/bots/api) and the Cloudflare Workers limits/bindings pages — re-check both before relying on any version-specific claim here; the Bot API moves fast.

External sources consulted (facts distilled, text original): the Rich
Messages field guide in nik-ti/agent-skills (license unclear — link-only:
https://github.com/nik-ti/agent-skills), production invariants from
mhanafi09051998/brain-ai (MIT), framework/RTL notes from
skills-il/developer-tools (MIT), and grammY webhook patterns from
VKirill/antigravity-for-claude-code (license unclear — link-only).

# Production checklist — Telegram bots

Run top to bottom before a release. Every item here has either bitten the
fleet in production or is a documented platform invariant.

## Ingestion

- [ ] Webhook set with `secret_token`; handler verifies
      `X-Telegram-Bot-Api-Secret-Token` on every POST and rejects others.
- [ ] `allowed_updates` limited to what the bot actually handles.
- [ ] Handler returns 200 fast; heavy work in `ctx.waitUntil` (or a queue).
- [ ] `update_id` dedupe in place — Telegram retries deliveries, and a
      retried paid action (AI call, post, payment) is a double charge.
- [ ] Stale-update age gate: updates minutes old (post-downtime backlog)
      are dropped, not executed against current state.
- [ ] No stack traces, secrets or internal ids in any error response.
- [ ] `getWebhookInfo` checked after deploy: correct URL, zero unexpected
      pending updates, no `last_error_message`.

## Loops and abuse

- [ ] Bot-to-bot: the bot ignores other bots by default; if Bot-to-Bot
      Communication Mode is enabled, replies carry a depth/loop guard
      and per-chat rate limiting.
- [ ] The bot never reacts to its own messages, edits or channel posts it
      just made (self-trigger check on sender id).
- [ ] Per-user rate limit on expensive actions (AI generation, search);
      a friendly refusal message, not silence.
- [ ] Callback debounce: rapid double-taps on the same button do not run
      the action twice (dedupe by callback id / last-action timestamp).
- [ ] Global send rate respected (~30/s); per-chat ~1/s; 429 responses
      honour `parameters.retry_after` with backoff, never a hot retry.

## Formatting and limits

- [ ] Every send path goes through the 4096-unit splitter (UTF-16 units,
      entity ranges adjusted per chunk, headroom below the limit).
- [ ] Captions respect the 1024-unit media caption limit separately.
- [ ] Entity offsets computed during assembly — no `indexOf` lookups on
      localized strings anywhere in the formatting layer.
- [ ] `callback_data` values are ASCII and ≤ 64 bytes; prefixes are
      namespaced per flow; stale buttons from older versions fail
      gracefully (answer + home screen), never crash.
- [ ] Rich Messages used only for fire-and-forget content (no edit path
      depends on them — `editMessageRichText` does not exist).
- [ ] RTL strings checked in a real client: mixed-direction lines,
      numbers and English terms render in the intended order.

## State and resources

- [ ] KV writes budgeted (free tier ~1,000/day): merged user record,
      ≤ ~2 writes per user message, TTLs on ephemeral keys.
- [ ] No per-message "tracking" writes; users are recorded once.
- [ ] Subrequest budget per invocation counted for fan-out work
      (broadcasts chunked across invocations, not one giant loop).
- [ ] CPU-heavy work (parsing, diffing, image handling) measured against
      the plan's CPU limit, not assumed free.

## Errors and recovery

- [ ] API errors classified: 4xx user errors surfaced to the user,
      429 backed off, 5xx/network retried once, everything logged with
      method + description.
- [ ] Provider chain: each attempt timed out (~20–25s), failures fall
      through to the next provider, total failure produces one honest
      user-facing message.
- [ ] Deploy is one command and reversible; the previous version can be
      restored without touching secrets or the webhook.
- [ ] Token rotation rehearsed: revoke → update secret → redeploy →
      `getMe` + `getWebhookInfo` verification.

## Live test matrix (before announcing)

- [ ] Every screen/flow walked in every shipped language.
- [ ] One over-limit message, one empty message, one sticker/GIF sent.
- [ ] Primary provider forced to fail; fallback verified end to end.
- [ ] Group behaviour: mention, reply, command, and (if enabled) a
      bot-to-bot exchange with the loop guard observed.
- [ ] Inline mode (if enabled): query in a foreign chat, result inserts
      correctly, no state leaked from private flow.

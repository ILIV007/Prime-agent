# Cookbook

*Original skills written in-house for this collection — recipes distilled from production work, not imported.*

Back to the [root README](../../README.md).

| Skill | What it does | Why it's here | Requires | Source |
|---|---|---|---|---|
| [telegram-bot-workers](telegram-bot-workers/) | Build production Telegram bots on Cloudflare Workers with the raw Bot API: secure webhooks, entity-based formatting, Rich Messages, edit-in-place menus, and KV state discipline. | The house recipe behind a working fleet of Telegram bots (channel AI, admin publisher, market poster, prompt optimizer). Every other bot skill out there assumes Python or a framework; this one covers the raw-API-on-Workers pattern those bots actually run on. | — | [ILIV007/prime-skill](https://github.com/ILIV007/prime-skill) @ 0ea9096 |
| [xdesign-export-builder](xdesign-export-builder/) | Build a working Telegram bot from an xDesign export zip: read spec.json as the source of truth, turn its steps into a state machine, and implement it on Cloudflare Workers or any webhook bot stack. | The design half of bot building had no skill: designers can now draw a bot in xDesign's no-code editor and an agent can implement it faithfully from the export, step for step, without re-deciding anything — the first skill that treats a bot design file as a build contract. | — | [Sir-MmD/xdesign](https://github.com/Sir-MmD/xdesign) @ 7ed1da0 |

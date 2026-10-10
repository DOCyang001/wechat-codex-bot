# Attribution and source versions

This repository is a Windows deployment integration distributed under GPL-3.0-or-later.

- `wechatbot-source/` is derived from **fanyuantaier/wechatbot-new**, commit `798490beb8602e5dc7d02ad4c79459491da86bf9`, retaining copyright notices and upstream LICENSE. Upstream derives from KouriChat / WeChatBot_WXAUTO_SE, copyright umaru and iwyxdxl. Source: <https://github.com/fanyuantaier/wechatbot-new>.
- **wechatauto-replica** is installed from commit `d6e61bea7f9c75906faa8b71d37ef3572fba2454`, not vendored as an opaque binary. Source: <https://github.com/fanyuantaier/wechatauto-replica>.
- **Codex CLI** is a separately installed OpenAI tool. Tested locally with version `0.159.2`; npm package `@openai/codex`. Source: <https://github.com/openai/codex>. Its authentication, model entitlements and quota are managed by the account provider.

Local modifications: loopback OpenAI-compatible Codex adapter; per-install account/allowlist settings; fresh history injection even with a voice profile; no-reply and error suppression; exact/unique contact resolution; send-time manual-reply check; text-only sending; listener readiness status; installer and owned-process start/stop scripts. No upstream executable, private chat archive, database key or authentication material is included.

The LICENSE at repository root and `wechatbot-source/LICENSE` retain the upstream GPL-3.0-or-later notice. Dependencies retain their respective upstream licenses.

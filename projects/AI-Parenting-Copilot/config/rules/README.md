<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 02:50:00
-->

# Rule Packs

Project rule packs are versioned YAML files loaded by `server.app.rule_engine.loader`.
Each pack must include `policy_type`, `domain`, `region`, `version`, `effective_from`,
`source`, `constants`, and `rules`. Optional `hash` can be used for tamper detection.

Current packs are deterministic development baselines, not medical advice. Rule content
must be reviewed and versioned before production use.

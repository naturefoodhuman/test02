<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-23 14:55:00
-->

# Browser Profiles

FORGE Network uses isolated browser profiles. The human daily Chrome profile must
never be used by agents.

## Profile classes

- `AI-Public`: public browsing / low-risk automation.
- `AI-Private-*`: manually logged-in, private read-only access.
- Daily human profile: out of scope and forbidden.

## Private profile rules

- Manual login only.
- Do not save passwords.
- Do not store payment information.
- Disable extensions.
- Use only allowed domains documented in each profile README.
- All content must pass InputSanitizer + PrivacyGateway before model use.
- Write actions require human approval.

<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-07-09 11:10:00
-->


# AI Parenting Copilot Android

Android-only React Native shell. This directory intentionally does not contain iOS code.

Current state:

- API client and navigation/theme skeleton are present.
- Auth/session, local event store, pending sync, and Quick Record candidate builder have pure TS logic.
- Native Gradle project and real RN dependency install are still pending local Android toolchain validation.

Suggested local commands once Android/RN toolchain is available:

```bash
cd projects/AI-Parenting-Copilot/android
npm install
npm run android
npm run test:static
```

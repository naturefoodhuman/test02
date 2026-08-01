<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode
创建时间（北京时间）：2026-08-01 03:50:00
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

# Native Android shell build smoke
cd android
./gradlew assembleDebug
```

`android/android/gradlew` is a bootstrap wrapper: it uses a committed Gradle wrapper jar when present, otherwise falls back to an installed `gradle` command or downloads the configured Gradle distribution into local `.gradle/bootstrap/` (gitignored).

## Native Android skeleton

The initial native Android project skeleton is under `android/android/`:

- `android/android/settings.gradle`
- `android/android/build.gradle`
- `android/android/app/build.gradle`
- `android/android/app/src/main/AndroidManifest.xml`
- `android/android/app/src/main/java/com/aiparentingcopilot/*`

This is a minimal Android shell for toolchain validation. The React Native bridge and full native modules remain blocked until Gradle/RN/device validation.

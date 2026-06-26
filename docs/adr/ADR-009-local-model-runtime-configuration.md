<!--
创建/修改该文件的LLM大模型：Arena.ai Agent Mode - Execution Lead Engineer
创建时间（北京时间）：2026-06-26 00:00:00
-->

# ADR-009: Local Model Runtime Configuration as SSOT

- **Status**: 已接受
- **Date**: 2026-06-26
- **Deciders**: User + Arena.ai Agent Mode
- **Related**: `config/model_runtime.yaml`, `_infra/model_runtime.py`, `scripts/forge-start.sh`, `_infra/smart_proxy.py`, `peer_review.llm_client`

## Context（背景）

Local model startup commands and performance flags were previously hardcoded in multiple places:

- `scripts/forge-start.sh`
- `_factory/patterns/peer-review/src/peer_review/llm_client.py`
- `_infra/smart_proxy.py` memory estimates

This made it difficult to tune MTPLX, Ollama and llama.cpp runtime flags, including:

- Ollama Flash Attention / KV cache compression;
- MTPLX runtime flags;
- llama.cpp MTP speculative decoding flags;
- model log paths and memory estimates;
- future runtime A/B tests.

The project requires strict traceability because it is used for safety-sensitive project development and accident/postmortem analysis.

## Decision（决策）

Create `config/model_runtime.yaml` as the Single Source of Truth for local model runtime configuration.

All local runtime command generation must go through `_infra/model_runtime.py` where practical.

The configuration covers:

- MTPLX model IDs, ports, logs, extra args;
- Ollama environment variables and model IDs;
- llama.cpp command flags including MTP speculative decoding;
- kill patterns;
- memory estimates;
- model source URLs.

## Rationale（理由）

- Runtime performance tuning must be auditable.
- Model launch flags should not be scattered through scripts.
- Ollama and llama.cpp flags need explicit, user-editable configuration.
- MTPLX MTP/streaming behavior is runtime-dependent and must be validated by diagnostics, not assumed from model names.
- Central config supports future A/B experiments and faster incident diagnosis.

## Consequences（影响）

Positive:

- Users can tune model startup flags without editing code.
- `scripts/forge-start.sh` and on-demand `SERVER_COMMANDS` are aligned.
- MTP/speculative decoding flags are visible and reviewable.
- Diagnostics can inspect the exact runtime configuration.

Negative / Cost:

- One more config file must be kept valid.
- If the config is wrong, model startup can fail globally.
- MTPLX CLI flags are still dependent on the locally installed MTPLX version; users must verify `mtplx quickstart --help` before adding flags.

## Implementation Notes

Implemented on 2026-06-26:

- `config/model_runtime.yaml`
- `_infra/model_runtime.py`
- `scripts/forge-start.sh` reads commands/env from config.
- `peer_review.llm_client.SERVER_COMMANDS` loads from config with fallback.
- `_infra/smart_proxy.py` reads memory estimates from config.
- `scripts/diagnostics/test_mtp_effectiveness.py` inspects commands and logs.

## Rollback Strategy（回滚方案）

If config loading fails, `peer_review.llm_client` keeps a historical fallback command table. For `forge-start.sh`, rollback by replacing `model_command` calls with the previous hardcoded command lines.

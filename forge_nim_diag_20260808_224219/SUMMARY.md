# FORGE NIM Diagnostic Summary

- generated_local: `2026-08-08 22:45:20 +0800`
- profile: `current`
- git_head_final: `272003d (HEAD -> main) 说明`
- output_dir: `/private/tmp/forge_nim_diag_20260808_224219`

## Applied env updates

```json
{}
```

## Curl probes

## Direct NVIDIA upstream probes

```json
[
  {
    "key_id": "key-1",
    "model": "z-ai/glm-5.2",
    "models_endpoint": {
      "method": "GET",
      "url": "https://integrate.api.nvidia.com/v1/models",
      "status": 200,
      "elapsed_s": 0.359,
      "error": "",
      "headers": {
        "Content-Type": "application/json"
      },
      "body_preview": "{\"object\":\"list\",\"data\":[{\"id\":\"01-ai/yi-large\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"01-ai\"},{\"id\":\"adept/fuyu-8b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"adept\"},{\"id\":\"ai21labs/jamba-1.5-large-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"ai21labs\"},{\"id\":\"aisingapore/sea-lion-7b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"aisingapore\"},{\"id\":\"baai/bge-m3\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"baai\"},{\"id\":\"bigcode/starcoder2-15b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"bigcode\"},{\"id\":\"databricks/dbrx-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"databricks\"},{\"id\":\"deepseek-ai/deepseek-coder-6.7b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"deepseek-ai\"},{\"id\":\"deepseek-ai/deepseek-v4-flash-0731\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"deepseek-ai\"},{\"id\":\"google/codegemma-1.1-7b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/codegemma-7b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/deplot\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/diffusiongemma-26b-a4b-it\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/gemma-2b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/gemma-3-12b-it\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/gemma-3-4b-it\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/gemma-4-31b-it\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"google/recurrentgemma-2b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"google\"},{\"id\":\"ibm/granite-3.0-3b-a800m-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"ibm\"},{\"id\":\"ibm/granite-3.0-8b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"ibm\"},{\"id\":\"ibm/granite-34b-code-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"ibm\"},{\"id\":\"ibm/granite-8b-code-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"ibm\"},{\"id\":\"meta/codellama-70b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.1-70b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.1-8b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.2-11b-vision-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.2-1b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.2-3b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.2-90b-vision-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-3.3-70b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama-guard-4-12b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"meta/llama2-70b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"meta\"},{\"id\":\"microsoft/kosmos-2\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"microsoft\"},{\"id\":\"microsoft/phi-3-vision-128k-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"microsoft\"},{\"id\":\"microsoft/phi-3.5-moe-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"microsoft\"},{\"id\":\"minimaxai/minimax-m3\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"minimaxai\"},{\"id\":\"mistralai/codestral-22b-instruct-v0.1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"mistralai\"},{\"id\":\"mistralai/mistral-7b-instruct-v0.3\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"mistralai\"},{\"id\":\"mistralai/mistral-large\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"mistralai\"},{\"id\":\"mistralai/mistral-large-2-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"mistralai\"},{\"id\":\"mistralai/mistral-nemotron\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"mistralai\"},{\"id\":\"mistralai/mixtral-8x22b-v0.1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"mistralai\"},{\"id\":\"moonshotai/kimi-k2.6\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"moonshotai\"},{\"id\":\"nv-mistralai/mistral-nemo-12b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nv-mistralai\"},{\"id\":\"nvidia/ai-synthetic-video-detector\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/cosmos-reason2-8b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/embed-qa-4\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/ising-calibration-1.5-31b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemoguard-8b-content-safety\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemoguard-8b-topic-control\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemotron-51b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemotron-70b-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemotron-nano-8b-v1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemotron-nano-vl-8b-v1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemotron-safety-guard-8b-v3\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.1-nemotron-ultra-253b-v1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.2-nv-embedqa-1b-v1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.3-nemotron-super-49b-v1\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-3.3-nemotron-super-49b-v1.5\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-nemotron-embed-1b-v2\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama-nemotron-embed-vl-1b-v2\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/llama3-chatqa-1.5-70b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/mistral-nemo-minitron-8b-8k-instruct\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/nemoretriever-parse\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/nemotron-3-embed-1b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/nemotron-3-nano-30b-a3b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/nemotron-3-super-120b-a12b\",\"object\":\"model\",\"created\":735790403,\"owned_by\":\"nvidia\"},{\"id\":\"nvidia/
```

## Final stats excerpt

```json
{
  "nim": {
    "request_count": 2,
    "retry_count": 2,
    "fallback_count": 0,
    "settings": {
      "upstream_base_url": "https://integrate.api.nvidia.com/v1",
      "primary_model": "z-ai/glm-5.2",
      "fallback_model": "deepseek-ai/DeepSeek-V4-Pro",
      "enable_fallback": false,
      "per_key_rpm": 35,
      "per_key_concurrency": 1,
      "max_attempts_per_request": 1,
      "read_timeout_seconds": 300.0,
      "request_wall_timeout_seconds": 360.0,
      "session_affinity": false
    },
    "pool": {
      "key_count": 2,
      "keys": [
        {
          "key_id": "key-1",
          "available_in_seconds": 0.0,
          "in_cooldown": false,
          "recent_rpm": 0,
          "rpm_limit": 35,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 0,
          "success_count": 0,
          "error_count": 1
        },
        {
          "key_id": "key-2",
          "available_in_seconds": 0.0,
          "in_cooldown": false,
          "recent_rpm": 0,
          "rpm_limit": 35,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 0,
          "success_count": 0,
          "error_count": 1
        }
      ],
      "affinity_size": 0
    }
  },
  "smart": {
    "active_requests": 0,
    "total_requests": 1,
    "total_errors": 1,
    "retry": {
      "local_retry_count": 0,
      "remote_retry_count": 2,
      "stream_remote_retry_count": 2,
      "retryable_status_codes": [
        429,
        502,
        503,
        504
      ],
      "retry_counters": {
        "429": 0,
        "502": 0,
        "503": 0,
        "504": 0
      }
    },
    "context_budget": {
      "max_tokens": 202752,
      "soft_tokens": 32000,
      "soft_ratio": 0.8,
      "hard_ratio": 0.95,
      "keep_recent_turns": 8,
      "trunc_tool_result_chars": 2000,
      "counters": {
        "pass": 1,
        "compacted": 0,
        "rejected": 0
      },
      "last": {
        "action": "pass",
        "est_before": 28,
        "est_after": 28
      }
    }
  }
}
```

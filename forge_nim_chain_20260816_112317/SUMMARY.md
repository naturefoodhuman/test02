# FORGE NIM Chain Monitor Summary

- generated_local: `2026-08-16 11:23:17 +0800`
- output_dir: `/private/tmp/forge_nim_chain_20260816_112317`

## Findings

### HIGH — NVIDIA_UPSTREAM_429_COOLDOWN

At least one NVIDIA key is in cooldown or has consecutive upstream 429s.

Recommendation: Treat this as upstream NVIDIA/free-tier pressure. Keep fallback disabled if policy requires it; reduce prompt size and keep FORGE_REMOTE_MAX_CONCURRENCY=1. Do not increase RPM.

```json
{
  "cooldown_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 178.788,
      "consecutive_429": 58
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 54.384,
      "consecutive_429": 3
    }
  ],
  "total_consecutive_429": 61
}
```

### HIGH — SMART_SEES_429_FROM_NIM

Smart Proxy has observed 429 responses from the NIM sidecar.

Recommendation: If running a version before abd6459, pull latest: NIM busy should be separated from true rate_limit. If still 429 after latest, inspect 4010 /stats cooldown fields.

```json
{
  "smart_retry_429_counter": 81
}
```

### MEDIUM — PROMPT_LARGE_OR_COMPACTED

Prompt/context is large enough to trigger or approach compaction.

Recommendation: Large prompts increase GLM-5.2 latency and 429 risk. If failures persist, reduce FORGE_CTX_SOFT_TOKENS or run /compact in Claude Code.

```json
{
  "est_before": 167480,
  "soft_tokens": 162201,
  "max_tokens": 902752,
  "last_context": {
    "action": "compacted",
    "est_before": 167480,
    "est_after": 105927
  }
}
```

## Sample summary

```json
{
  "sample_count": 1,
  "started_local": "2026-08-16 11:23:17 +0800",
  "ended_local": "2026-08-16 11:23:17 +0800",
  "smart_total_requests_delta": 0,
  "smart_total_errors_delta": 0,
  "nim_request_count_delta": 0,
  "nim_retry_count_delta": 0,
  "final_active_requests": 5,
  "final_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 178.788,
      "in_cooldown": true,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 58,
      "success_count": 0,
      "error_count": 58
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 54.384,
      "in_cooldown": true,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 3,
      "success_count": 99,
      "error_count": 52
    }
  ]
}
```

## Latest snapshot excerpt

```json
{
  "smart": {
    "active_requests": 5,
    "total_requests": 147,
    "total_errors": 43,
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
        "429": 81,
        "502": 0,
        "503": 0,
        "504": 0
      }
    },
    "circuit_breaker": {
      "state": "closed",
      "consecutive_429": 0,
      "trip_threshold": 2,
      "cooldown_seconds": 45.0,
      "opened_at": 0.0
    },
    "context_budget": {
      "max_tokens": 902752,
      "soft_tokens": 162201,
      "soft_ratio": 0.8,
      "hard_ratio": 0.95,
      "keep_recent_turns": 4,
      "trunc_tool_result_chars": 1200,
      "counters": {
        "pass": 125,
        "compacted": 22,
        "rejected": 0
      },
      "last": {
        "action": "compacted",
        "est_before": 167480,
        "est_after": 105927
      }
    }
  },
  "nim": {
    "request_count": 210,
    "retry_count": 110,
    "settings": {
      "upstream_base_url": "https://integrate.api.nvidia.com/v1",
      "primary_model": "z-ai/glm-5.2",
      "fallback_model": "deepseek-ai/DeepSeek-V4-Pro",
      "enable_fallback": false,
      "per_key_rpm": 20,
      "per_key_concurrency": 1,
      "max_attempts_per_request": 1,
      "read_timeout_seconds": 1200.0,
      "request_wall_timeout_seconds": 1500.0,
      "session_affinity": false
    },
    "pool": {
      "key_count": 2,
      "keys": [
        {
          "key_id": "key-1",
          "available_in_seconds": 178.788,
          "in_cooldown": true,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 58,
          "success_count": 0,
          "error_count": 58
        },
        {
          "key_id": "key-2",
          "available_in_seconds": 54.384,
          "in_cooldown": true,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 3,
          "success_count": 99,
          "error_count": 52
        }
      ],
      "affinity_size": 0
    }
  }
}
```

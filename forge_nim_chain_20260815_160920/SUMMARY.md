# FORGE NIM Chain Monitor Summary

- generated_local: `2026-08-15 16:19:21 +0800`
- output_dir: `/private/tmp/forge_nim_chain_20260815_160920`

## Findings

### HIGH — NVIDIA_UPSTREAM_429_COOLDOWN

At least one NVIDIA key is in cooldown or has consecutive upstream 429s.

Recommendation: Treat this as upstream NVIDIA/free-tier pressure. Keep fallback disabled if policy requires it; reduce prompt size and keep FORGE_REMOTE_MAX_CONCURRENCY=1. Do not increase RPM.

```json
{
  "cooldown_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 335.552,
      "consecutive_429": 1
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 335.836,
      "consecutive_429": 1
    }
  ],
  "total_consecutive_429": 2
}
```

### HIGH — SMART_SEES_429_FROM_NIM

Smart Proxy has observed 429 responses from the NIM sidecar.

Recommendation: If running a version before abd6459, pull latest: NIM busy should be separated from true rate_limit. If still 429 after latest, inspect 4010 /stats cooldown fields.

```json
{
  "smart_retry_429_counter": 11
}
```

## Sample summary

```json
{
  "sample_count": 41,
  "started_local": "2026-08-15 16:09:20 +0800",
  "ended_local": "2026-08-15 16:19:21 +0800",
  "smart_total_requests_delta": 31,
  "smart_total_errors_delta": 12,
  "nim_request_count_delta": 32,
  "nim_retry_count_delta": 2,
  "final_active_requests": 0,
  "final_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 335.552,
      "in_cooldown": true,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 1,
      "success_count": 10,
      "error_count": 1
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 335.836,
      "in_cooldown": true,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 1,
      "success_count": 10,
      "error_count": 1
    }
  ]
}
```

## Latest snapshot excerpt

```json
{
  "smart": {
    "active_requests": 0,
    "total_requests": 32,
    "total_errors": 12,
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
        "429": 11,
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
        "pass": 32,
        "compacted": 0,
        "rejected": 0
      },
      "last": {
        "action": "pass",
        "est_before": 108019,
        "est_after": 108019
      }
    }
  },
  "nim": {
    "request_count": 32,
    "retry_count": 2,
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
          "available_in_seconds": 335.552,
          "in_cooldown": true,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 1,
          "success_count": 10,
          "error_count": 1
        },
        {
          "key_id": "key-2",
          "available_in_seconds": 335.836,
          "in_cooldown": true,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 1,
          "success_count": 10,
          "error_count": 1
        }
      ],
      "affinity_size": 0
    }
  }
}
```

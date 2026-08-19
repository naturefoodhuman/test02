# FORGE NIM Chain Monitor Summary

- generated_local: `2026-08-19 13:47:52 +0800`
- output_dir: `/private/tmp/forge_nim_chain_20260819_133751`

## Findings

### HIGH — NVIDIA_UPSTREAM_429_COOLDOWN

At least one NVIDIA key is in cooldown or has consecutive upstream 429s.

Recommendation: Treat this as upstream NVIDIA/free-tier pressure. Keep fallback disabled if policy requires it; reduce prompt size and keep FORGE_REMOTE_MAX_CONCURRENCY=1. Do not increase RPM.

```json
{
  "cooldown_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 397.109,
      "consecutive_429": 3
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 494.977,
      "consecutive_429": 9
    }
  ],
  "total_consecutive_429": 12
}
```

### HIGH — SMART_SEES_429_FROM_NIM

Smart Proxy has observed 429 responses from the NIM sidecar.

Recommendation: If running a version before abd6459, pull latest: NIM busy should be separated from true rate_limit. If still 429 after latest, inspect 4010 /stats cooldown fields.

```json
{
  "smart_retry_429_counter": 13
}
```

## Sample summary

```json
{
  "sample_count": 41,
  "started_local": "2026-08-19 13:37:51 +0800",
  "ended_local": "2026-08-19 13:47:52 +0800",
  "smart_total_requests_delta": 2,
  "smart_total_errors_delta": 1,
  "nim_request_count_delta": 3,
  "nim_retry_count_delta": 2,
  "final_active_requests": 1,
  "final_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 397.109,
      "in_cooldown": true,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 3,
      "success_count": 21,
      "error_count": 18
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 494.977,
      "in_cooldown": true,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 9,
      "success_count": 21,
      "error_count": 18
    }
  ]
}
```

## Latest snapshot excerpt

```json
{
  "smart": {
    "active_requests": 1,
    "total_requests": 51,
    "total_errors": 8,
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
        "429": 13,
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
        "pass": 51,
        "compacted": 0,
        "rejected": 0
      },
      "last": {
        "action": "pass",
        "est_before": 98676,
        "est_after": 98676
      }
    }
  },
  "nim": {
    "request_count": 79,
    "retry_count": 36,
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
          "available_in_seconds": 397.109,
          "in_cooldown": true,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 3,
          "success_count": 21,
          "error_count": 18
        },
        {
          "key_id": "key-2",
          "available_in_seconds": 494.977,
          "in_cooldown": true,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 9,
          "success_count": 21,
          "error_count": 18
        }
      ],
      "affinity_size": 0
    }
  }
}
```

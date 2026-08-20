# FORGE NIM Chain Monitor Summary

- generated_local: `2026-08-20 11:56:43 +0800`
- output_dir: `/private/tmp/forge_nim_chain_20260820_114642`

## Findings

### HIGH — NVIDIA_UPSTREAM_429_COOLDOWN

At least one NVIDIA key is in cooldown or has consecutive upstream 429s.

Recommendation: Treat this as upstream NVIDIA/free-tier pressure. Keep fallback disabled if policy requires it; reduce prompt size and keep FORGE_REMOTE_MAX_CONCURRENCY=1. Do not increase RPM.

```json
{
  "cooldown_keys": [],
  "total_consecutive_429": 80
}
```

### MEDIUM — NIM_KEYS_BUSY

One or more NIM keys are occupied by long-running upstream requests.

Recommendation: This is expected when GLM-5.2 takes minutes. Ensure NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST=1 and consider NIM_PROXY_QUEUE_TIMEOUT_SECONDS=120 so new turns fail fast with busy instead of waiting forever.

```json
{
  "in_flight_total": 1,
  "locked_keys": [
    {
      "key_id": "key-2",
      "in_flight": 1,
      "success_count": 0,
      "error_count": 80
    }
  ]
}
```

### HIGH — SMART_SEES_429_FROM_NIM

Smart Proxy has observed 429 responses from the NIM sidecar.

Recommendation: If running a version before abd6459, pull latest: NIM busy should be separated from true rate_limit. If still 429 after latest, inspect 4010 /stats cooldown fields.

```json
{
  "smart_retry_429_counter": 15
}
```

### MEDIUM — PROMPT_LARGE_OR_COMPACTED

Prompt/context is large enough to trigger or approach compaction.

Recommendation: Large prompts increase GLM-5.2 latency and 429 risk. If failures persist, reduce FORGE_CTX_SOFT_TOKENS or run /compact in Claude Code.

```json
{
  "est_before": 228119,
  "soft_tokens": 162201,
  "max_tokens": 902752,
  "last_context": {
    "action": "compacted",
    "est_before": 228119,
    "est_after": 168298
  }
}
```

### MEDIUM — READ_TIMEOUT_IN_LOGS

Recent logs include ReadTimeout events.

Recommendation: This usually indicates NVIDIA GLM-5.2 slow/overloaded responses. Long timeout may help but cannot guarantee success.

```json
{
  "smart": {
    "http_429": 28,
    "http_503": 0,
    "http_504": 38,
    "read_timeout": 2,
    "remote_protocol_error": 0,
    "no_key_available": 0,
    "busy": 0,
    "rate_limit": 0,
    "client_disconnect": 0,
    "bind_in_use": 0,
    "context_compacted": 56,
    "context_rejected": 0
  },
  "nim": {
    "http_429": 30,
    "http_503": 0,
    "http_504": 16,
    "read_timeout": 0,
    "remote_protocol_error": 0,
    "no_key_available": 0,
    "busy": 0,
    "rate_limit": 0,
    "client_disconnect": 0,
    "bind_in_use": 0,
    "context_compacted": 0,
    "context_rejected": 0
  }
}
```

### HIGH — REPEATED_IDENTICAL_REQUESTS

Request event log shows repeated identical request payloads, likely client retries after timeouts.

Recommendation: Pull latest Smart Proxy with FORGE_REMOTE_SINGLEFLIGHT=1 to deduplicate identical non-stream retries; if repeats persist, inspect whether Claude Code/Feishu client is resubmitting after its own timeout.

```json
{
  "event_count": 500,
  "request_start_count": 235,
  "request_finish_count": 196,
  "request_error_count": 26,
  "singleflight_join_count": 25,
  "repeated_requests": [
    {
      "count": 11,
      "latest_user_sha256": "<empty>",
      "body_bytes": 967634,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-20 06:26:31",
      "last_local_time": "2026-08-20 07:13:09",
      "request_ids": [
        "079c817b2cfd",
        "9223ae89b532",
        "2b808a0056e5",
        "e5cbad60665f",
        "f157c66f03cb",
        "34c888fd7043",
        "48e9a0ad46dc",
        "0bb1691d70a0",
        "f8032f326744",
        "34d9fda9f5ad"
      ],
      "latest_user_chars": 0
    },
    {
      "count": 11,
      "latest_user_sha256": "64847cc3653fb4a0",
      "body_bytes": 969356,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-20 07:54:39",
      "last_local_time": "2026-08-20 08:38:28",
      "request_ids": [
        "db3ce58ebad0",
        "b223e3ace975",
        "a69a7c987a59",
        "632848764eb0",
        "303c9f1c3150",
        "5ef7286ebe80",
        "01f767802a24",
        "884db301e91f",
        "649176406f6f",
        "ac7823ae3016"
      ],
      "latest_user_chars": 1567
    },
    {
      "count": 6,
      "latest_user_sha256": "<empty>",
      "body_bytes": 883329,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-20 04:30:37",
      "last_local_time": "2026-08-20 04:50:19",
      "request_ids": [
        "127317e50570",
        "573f79075a86",
        "a4a3c8f59e6b",
        "e3b71c5f9f55",
        "ad630d04180b",
        "ca3f1fd08bd7"
      ],
      "latest_user_chars": 0
    }
  ],
  "error_types": {
    "429": 14,
    "TimeoutError: ": 12
  }
}
```

## Sample summary

```json
{
  "sample_count": 41,
  "started_local": "2026-08-20 11:46:42 +0800",
  "ended_local": "2026-08-20 11:56:43 +0800",
  "smart_total_requests_delta": 0,
  "smart_total_errors_delta": 0,
  "nim_request_count_delta": 0,
  "nim_retry_count_delta": 0,
  "final_active_requests": 1,
  "final_keys": [
    {
      "key_id": "key-1",
      "available_in_seconds": 0.0,
      "in_cooldown": false,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 0,
      "success_count": 226,
      "error_count": 38
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 0.0,
      "in_cooldown": false,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 1,
      "semaphore_locked": true,
      "consecutive_429": 80,
      "success_count": 0,
      "error_count": 80
    }
  ]
}
```

## Latest snapshot excerpt

```json
{
  "smart": {
    "active_requests": 1,
    "total_requests": 312,
    "total_errors": 66,
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
        "429": 15,
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
        "pass": 169,
        "compacted": 143,
        "rejected": 0
      },
      "last": {
        "action": "compacted",
        "est_before": 228119,
        "est_after": 168298
      }
    }
  },
  "nim": {
    "request_count": 349,
    "retry_count": 118,
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
          "available_in_seconds": 0.0,
          "in_cooldown": false,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 0,
          "success_count": 226,
          "error_count": 38
        },
        {
          "key_id": "key-2",
          "available_in_seconds": 0.0,
          "in_cooldown": false,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 1,
          "semaphore_locked": true,
          "consecutive_429": 80,
          "success_count": 0,
          "error_count": 80
        }
      ],
      "affinity_size": 0
    }
  }
}
```

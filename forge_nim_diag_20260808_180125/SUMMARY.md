# FORGE NIM Diagnostic Summary

- generated_local: `2026-08-08 18:01:30 +0800`
- profile: `timeout-a`
- git_head_final: `e444936 (HEAD -> main, origin/main, origin/HEAD) fix(infra): kill stale forge-start during diagnostics`
- output_dir: `/private/tmp/forge_nim_diag_20260808_180125`

## Applied env updates

```json
{
  "FORGE_USE_NIM_PROXY": "1",
  "NIM_PROXY_READ_TIMEOUT_SECONDS": "300",
  "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS": "360",
  "NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST": "1",
  "NIM_PROXY_ENABLE_FALLBACK": "0",
  "FORGE_REMOTE_MAX_CONCURRENCY": "1",
  "NIM_PROXY_PER_KEY_CONCURRENCY": "1"
}
```

## Curl probes

### curl_4010_nonstream

- trace: `TRACE-CURL4010-20260808-180128`
- start: `2026-08-08 18:01:28 +0800`
- end: `2026-08-08 18:01:29 +0800`
- elapsed_s: `0.838`
- metrics: `{"http_code": 404, "time_total": 0.826265, "time_starttransfer": 0.82624, "remote_ip": "127.0.0.1"}`
- response_preview: ``

### curl_4000_nonstream

- trace: `TRACE-CURL4000-20260808-180129`
- start: `2026-08-08 18:01:29 +0800`
- end: `2026-08-08 18:01:29 +0800`
- elapsed_s: `0.577`
- metrics: `{"http_code": 504, "time_total": 0.562106, "time_starttransfer": 0.561309, "remote_ip": "127.0.0.1"}`
- response_preview: `{"detail":"Backend failed: HTTP 404: "}`

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
          "recent_rpm": 1,
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
          "recent_rpm": 1,
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

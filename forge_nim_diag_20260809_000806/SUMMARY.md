# FORGE NIM Diagnostic Summary

- generated_local: `2026-08-09 00:20:08 +0800`
- profile: `glm-slow`
- git_head_final: `0d00272 (HEAD -> main) 说明`
- output_dir: `/private/tmp/forge_nim_diag_20260809_000806`

## Applied env updates

```json
{
  "FORGE_USE_NIM_PROXY": "1",
  "NIM_PROXY_READ_TIMEOUT_SECONDS": "360",
  "NIM_PROXY_REQUEST_WALL_TIMEOUT_SECONDS": "600",
  "NIM_PROXY_MAX_ATTEMPTS_PER_REQUEST": "1",
  "NIM_PROXY_ENABLE_FALLBACK": "0",
  "FORGE_REMOTE_MAX_CONCURRENCY": "1",
  "NIM_PROXY_PER_KEY_CONCURRENCY": "1",
  "FORGE_CTX_SOFT_TOKENS": "12000",
  "FORGE_CTX_KEEP_RECENT_TURNS": "4",
  "FORGE_CTX_TRUNC_TOOL_RESULT_CHARS": "800"
}
```

## Curl probes

### curl_4010_nonstream

- trace: `TRACE-CURL4010-20260809-000807`
- start: `2026-08-09 00:08:07 +0800`
- end: `2026-08-09 00:14:08 +0800`
- elapsed_s: `360.251`
- metrics: `{"http_code": 504, "time_total": 360.239478, "time_starttransfer": 360.238974, "remote_ip": "127.0.0.1"}`
- response_preview: `{"error": {"message": "ReadTimeout('')", "type": "ReadTimeout", "model": "z-ai/glm-5.2"}}`

### curl_4000_nonstream

- trace: `TRACE-CURL4000-20260809-001408`
- start: `2026-08-09 00:14:08 +0800`
- end: `2026-08-09 00:20:08 +0800`
- elapsed_s: `360.302`
- metrics: `{"http_code": 504, "time_total": 360.289663, "time_starttransfer": 360.288816, "remote_ip": "127.0.0.1"}`
- response_preview: `{"detail":"Backend failed: HTTP 504: {\"error\": {\"message\": \"ReadTimeout('')\", \"type\": \"ReadTimeout\", \"model\": \"z-ai/glm-5.2\"}}"}`

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
      "read_timeout_seconds": 360.0,
      "request_wall_timeout_seconds": 600.0,
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
        "504": 1
      }
    },
    "context_budget": {
      "max_tokens": 202752,
      "soft_tokens": 12000,
      "soft_ratio": 0.8,
      "hard_ratio": 0.95,
      "keep_recent_turns": 4,
      "trunc_tool_result_chars": 800,
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

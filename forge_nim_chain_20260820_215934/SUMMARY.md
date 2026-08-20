# FORGE NIM Chain Monitor Summary

- generated_local: `2026-08-20 21:59:35 +0800`
- output_dir: `/private/tmp/forge_nim_chain_20260820_215934`

## Findings

### MEDIUM — READ_TIMEOUT_IN_LOGS

Recent logs include ReadTimeout events.

Recommendation: This usually indicates NVIDIA GLM-5.2 slow/overloaded responses. Long timeout may help but cannot guarantee success.

```json
{
  "smart": {
    "http_429": 0,
    "http_503": 0,
    "http_504": 0,
    "read_timeout": 4,
    "remote_protocol_error": 0,
    "no_key_available": 0,
    "busy": 0,
    "rate_limit": 0,
    "client_disconnect": 1,
    "bind_in_use": 0,
    "context_compacted": 0,
    "context_rejected": 0
  },
  "nim": {
    "http_429": 0,
    "http_503": 0,
    "http_504": 0,
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
  "event_count": 2000,
  "request_start_count": 968,
  "request_finish_count": 786,
  "request_error_count": 130,
  "singleflight_join_count": 66,
  "repeated_requests": [
    {
      "count": 11,
      "latest_user_sha256": "<empty>",
      "body_bytes": 3880330,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-18 04:55:56",
      "last_local_time": "2026-08-18 05:48:13",
      "request_ids": [
        "bc217c271d5b",
        "d61a36ed011d",
        "75a679a68619",
        "a7921256fe38",
        "5af3c113ed70",
        "4e90b42883a1",
        "4a8622d6f2f5",
        "1b7be1fd578e",
        "06d4ce69de38",
        "1abaf921d844"
      ],
      "latest_user_chars": 0
    },
    {
      "count": 11,
      "latest_user_sha256": "7847fe3a7f12048c",
      "body_bytes": 104464,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-18 06:29:05",
      "last_local_time": "2026-08-18 07:21:34",
      "request_ids": [
        "bb71a16fad24",
        "99bef117dfdb",
        "0d4288a88094",
        "05868d5e41d3",
        "d85712baf25e",
        "ca22c7f4baa8",
        "4ba69eaedeb4",
        "c26aa024fda4",
        "338d562eb72f",
        "521ebfdd5075"
      ],
      "latest_user_chars": 9417
    },
    {
      "count": 11,
      "latest_user_sha256": "1c0bf3b453e8c0b3",
      "body_bytes": 104498,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-18 09:02:33",
      "last_local_time": "2026-08-18 09:55:41",
      "request_ids": [
        "c5f2b6c098ec",
        "c186e2000ece",
        "ec42c0b94ee0",
        "3698fd3cd4f6",
        "3f5ba53ed5b8",
        "14ef7b52558e",
        "128a3eb74787",
        "2c02c92faf7a",
        "683ee5396bf1",
        "5faad07802a3"
      ],
      "latest_user_chars": 9420
    },
    {
      "count": 11,
      "latest_user_sha256": "a4c95b88d1872d06",
      "body_bytes": 104532,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-18 22:27:50",
      "last_local_time": "2026-08-18 23:20:47",
      "request_ids": [
        "5ebdaab2b0e2",
        "a682b1a47620",
        "2cab0415aecc",
        "010aa245c74e",
        "eff4719fe64e",
        "d29d0eeb0134",
        "1e03de2a0800",
        "c7448ded5fff",
        "5e3f8d6ca56a",
        "ac753caee059"
      ],
      "latest_user_chars": 9423
    },
    {
      "count": 11,
      "latest_user_sha256": "580ddc07e50f15c1",
      "body_bytes": 102238,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-19 00:49:56",
      "last_local_time": "2026-08-19 01:42:40",
      "request_ids": [
        "083fe3ea188d",
        "f766387e247d",
        "c4c63b4ce412",
        "1d1e47413216",
        "fcde238ecdbd",
        "03376ad89b16",
        "bf188b3448b6",
        "1d6be9de8f8f",
        "865cafd51905",
        "b3a6565f7a0c"
      ],
      "latest_user_chars": 7435
    },
    {
      "count": 11,
      "latest_user_sha256": "<empty>",
      "body_bytes": 463860,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-19 12:33:38",
      "last_local_time": "2026-08-19 13:26:32",
      "request_ids": [
        "ddb1c35dd9b1",
        "f96312cffb93",
        "02f415cd7401",
        "88e35c880892",
        "a173e9b37546",
        "65396eb665eb",
        "db97e837075a",
        "6e18f031e39f",
        "efb1a1ee1b2a",
        "6b9355e3bb49"
      ],
      "latest_user_chars": 0
    },
    {
      "count": 11,
      "latest_user_sha256": "<empty>",
      "body_bytes": 469986,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-19 14:16:23",
      "last_local_time": "2026-08-19 15:07:55",
      "request_ids": [
        "77442c394893",
        "8ea33fb582bb",
        "414a2a28fe24",
        "3465c78d6749",
        "18c531e1cc93",
        "3852c10fce74",
        "75db4f4b8be3",
        "184bca5247f5",
        "f7b2b70b0749",
        "9888ff81d9df"
      ],
      "latest_user_chars": 0
    },
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
      "count": 11,
      "latest_user_sha256": "2f59ea9dcbc75071",
      "body_bytes": 969390,
      "stream": false,
      "model": "claude-opus-4-8",
      "path": "/v1/messages",
      "first_local_time": "2026-08-20 12:15:22",
      "last_local_time": "2026-08-20 13:03:56",
      "request_ids": [
        "ecbf645a3d97",
        "43906f0e16b0",
        "787b8bc6e16c",
        "bffa43f712ba",
        "07ea03273d50",
        "1fef9fe99341",
        "2c473709f8f2",
        "4b0c5452c964",
        "ce263aa9d793",
        "3d8e0ab001f4"
      ],
      "latest_user_chars": 1570
    }
  ],
  "error_types": {
    "429": 82,
    "TimeoutError: ": 46,
    "400": 2
  }
}
```

## Sample summary

```json
{
  "sample_count": 1,
  "started_local": "2026-08-20 21:59:35 +0800",
  "ended_local": "2026-08-20 21:59:35 +0800",
  "smart_total_requests_delta": 0,
  "smart_total_errors_delta": 0,
  "nim_request_count_delta": 0,
  "nim_retry_count_delta": 0,
  "final_active_requests": 0,
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
      "success_count": 0,
      "error_count": 3
    },
    {
      "key_id": "key-2",
      "available_in_seconds": 0.0,
      "in_cooldown": false,
      "recent_rpm": 0,
      "rpm_limit": 20,
      "concurrency_limit": 1,
      "in_flight": 0,
      "semaphore_locked": false,
      "consecutive_429": 0,
      "success_count": 0,
      "error_count": 2
    }
  ]
}
```

## Latest snapshot excerpt

```json
{
  "smart": {
    "active_requests": 0,
    "total_requests": 12,
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
        "429": 0,
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
        "pass": 12,
        "compacted": 0,
        "rejected": 0
      },
      "last": {
        "action": "pass",
        "est_before": 7479,
        "est_after": 7479
      }
    }
  },
  "nim": {
    "request_count": 5,
    "retry_count": 5,
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
          "success_count": 0,
          "error_count": 3
        },
        {
          "key_id": "key-2",
          "available_in_seconds": 0.0,
          "in_cooldown": false,
          "recent_rpm": 0,
          "rpm_limit": 20,
          "concurrency_limit": 1,
          "in_flight": 0,
          "semaphore_locked": false,
          "consecutive_429": 0,
          "success_count": 0,
          "error_count": 2
        }
      ],
      "affinity_size": 0
    }
  }
}
```

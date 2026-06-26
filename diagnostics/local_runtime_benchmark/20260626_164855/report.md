# Local Runtime Benchmark Report

Generated: 20260626_164855

## Summary Table

| profile | prompt | stream | client_s | first_delta_s | prompt_tokens | completion_tokens | mtplx_elapsed_s | tok_s | e2e_tok_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mtp_depth3 | medium_state_machine | False | 44.74 | - | 22 | 208 | 24.41 | 8.72 | 8.52 |
| no_mtp | medium_state_machine | False | 54.46 | - | 22 | 285 | 29.10 | 10.01 | 9.79 |

## Interpretation Notes

- Compare rows only when prompt and completion length are similar.
- Short prompts may favor no-MTP because draft/verify overhead can dominate.
- MTP benefits should be judged on repeated medium/long generations and stable token counts.
- Streaming first_delta includes on-demand model startup if 8080 was not already loaded.

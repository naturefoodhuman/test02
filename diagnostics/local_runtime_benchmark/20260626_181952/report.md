# Local Runtime Benchmark Report

Generated: 20260626_181952

## Raw Runs

| profile | prompt | repeat | stream | client_s | first_delta_s | prompt_tokens | completion_tokens | mtplx_elapsed_s | tok_s | e2e_tok_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mtp_depth3 | controlled_medium | 1 | False | 43.66 | - | 101 | 181 | 23.30 | 8.35 | 7.77 |
| mtp_depth3 | controlled_medium | 2 | False | 15.50 | - | 101 | 113 | 15.43 | 8.36 | 7.32 |
| mtp_depth3 | controlled_long_context | 1 | False | 58.01 | - | 2625 | 166 | 57.93 | 9.28 | 2.87 |
| mtp_depth3 | controlled_long_context | 2 | False | 15.76 | - | 2625 | 144 | 15.68 | 9.94 | 9.18 |
| no_mtp | controlled_medium | 1 | False | 36.11 | - | 101 | 111 | 12.20 | 10.53 | 9.10 |
| no_mtp | controlled_medium | 2 | False | 23.35 | - | 101 | 164 | 18.63 | 9.81 | 8.80 |
| no_mtp | controlled_long_context | 1 | False | 101.13 | - | 2625 | 183 | 58.60 | 9.43 | 3.12 |
| no_mtp | controlled_long_context | 2 | False | 64.73 | - | 2625 | 201 | 59.61 | 9.37 | 3.37 |
| mtp_depth3_kv_q8 | controlled_medium | 1 | False | 40.02 | - | 101 | 161 | 19.54 | 9.04 | 8.24 |
| mtp_depth3_kv_q8 | controlled_medium | 2 | False | 20.57 | - | 101 | 125 | 16.27 | 8.76 | 7.68 |
| mtp_depth3_kv_q8 | controlled_long_context | 1 | False | 55.98 | - | 2625 | 144 | 55.90 | 9.34 | 2.58 |
| mtp_depth3_kv_q8 | controlled_long_context | 2 | False | 18.55 | - | 2625 | 171 | 18.46 | 9.97 | 9.26 |
| mtp_depth3_kv_q4 | controlled_medium | 1 | False | 40.23 | - | 101 | 156 | 19.90 | 8.56 | 7.84 |
| mtp_depth3_kv_q4 | controlled_medium | 2 | False | 16.02 | - | 101 | 120 | 15.94 | 8.57 | 7.53 |
| mtp_depth3_kv_q4 | controlled_long_context | 1 | False | 55.41 | - | 2625 | 141 | 55.33 | 8.73 | 2.55 |
| mtp_depth3_kv_q4 | controlled_long_context | 2 | False | 17.77 | - | 2625 | 153 | 17.69 | 9.33 | 8.65 |

## Aggregates

| profile | prompt | n | client_s_mean | client_s_std | completion_mean | mtplx_elapsed_mean | tok_s_mean | e2e_tok_s_mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| mtp_depth3 | controlled_medium | 2 | 29.58 | 19.91 | 147.0 | 19.37 | 8.35 | 7.55 |
| mtp_depth3 | controlled_long_context | 2 | 36.89 | 29.87 | 155.0 | 36.80 | 9.61 | 6.02 |
| no_mtp | controlled_medium | 2 | 29.73 | 9.02 | 137.5 | 15.41 | 10.17 | 8.95 |
| no_mtp | controlled_long_context | 2 | 82.93 | 25.74 | 192.0 | 59.10 | 9.40 | 3.25 |
| mtp_depth3_kv_q8 | controlled_medium | 2 | 30.29 | 13.76 | 143.0 | 17.91 | 8.90 | 7.96 |
| mtp_depth3_kv_q8 | controlled_long_context | 2 | 37.27 | 26.47 | 157.5 | 37.18 | 9.66 | 5.92 |
| mtp_depth3_kv_q4 | controlled_medium | 2 | 28.12 | 17.12 | 138.0 | 17.92 | 8.56 | 7.68 |
| mtp_depth3_kv_q4 | controlled_long_context | 2 | 36.59 | 26.61 | 147.0 | 36.51 | 9.03 | 5.60 |

## Interpretation Notes

- Compare profiles within the same prompt and repeat set.
- Completion length still matters; prefer aggregate e2e_tok_s and mtplx_elapsed together.
- If q4/q8 quality differs, do not choose solely by speed.
- Streaming diagnostics are saved per profile in test_local_streaming.txt.

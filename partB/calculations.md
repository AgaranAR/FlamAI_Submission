# Part B — Capacity Reconciliation

## B1 — KV-cache bytes/token and max concurrent sequences

```
bytes/token = 2 (K,V) x layers x kv_heads x head_dim x bytes_per_elem(fp16)
            = 2 x 28 x 8 x 128 x 2
            = 114,688 bytes = 112.0 KiB/token
```

```
usable GPU mem = 24 GB x 0.92 (gpu_memory_utilization) = 22.08 GB
weights        = 4.2e9 params x 2 bytes (fp16)          = 8.4 GB
non-KV overhead (given)                                 = 1.6 GB
KV budget      = 22.08 - 8.4 - 1.6                       = 12.08 GB

max total KV tokens = 12.08e9 / 114,688       ≈ 105,329 tokens
max concurrent 4096-token sequences           ≈ 25.7
```

**Check against bench_log.csv:** `kv_cache_util` = 0.93 at batch=24
(no preemption), and `preempted_seqs` first appears at batch=32 (7 seqs).
Predicted ceiling (~25.7) sits exactly between the last clean batch (24)
and the first batch that overflows (32) — matches.

## B2 — the anomaly (long-context sweep, prompt_len=3584)

reported_tok_s by batch: 565 (b4) -> 903 (b8) -> 1311 (b16) -> **1607 (b24,
peak)** -> 1384 (b32, drops) -> 1298 (b48, drops further)

This contradicts naive "throughput scales with batch." Mechanism, from the
log columns directly:
- `kv_cache_util`: 0.93 (b24) -> 0.97 (b32) -> 0.97 (b48) — saturated right
  at b24, matching the B1 ceiling of ~25.7 sequences.
- `preempted_seqs`: 0 -> 7 -> 23 — scheduler is evicting sequences that
  don't fit in KV cache and recomputing their prefill on reschedule, which
  burns GPU cycles without producing new output tokens.

**Proposed change:** cap long-context batch size at ~24 (the computed
ceiling), or move KV cache to fp8 precision — halves bytes/token, roughly
doubles capacity to ~51 sequences, which would remove preemption at batch
48 entirely (predicted, not yet measured — flag this as an assumption to
validate with a follow-up run).

## B3 — the "one column" misreading

Verified `reported_tok_s` formula exactly against every row in the log:
```
reported_tok_s == (prompt_len + gen_len) x num_requests / wall_clock_s
```
(matches to 1 decimal on all 13 rows — this is not approximate, it's exact).
This counts prefill tokens (cheap, computed in one parallel forward pass)
as if they cost the same as decode tokens (expensive, one sequential step
per token) — so longer prompts mechanically inflate the number.

**Honest goodput for the batch=24, prompt=3584 row, two independent
methods:**
```
Method 1 (wall-clock, generated tokens only):
  gen_len x num_requests / wall_clock_s = 512 x 24 / 61.16 = 200.9 tok/s

Method 2 (inter-token latency implied):
  batch_size / itl_ms_p50(seconds) = 24 / 0.09607 = 249.8 tok/s
```
Both are 6.5-8x below the reported 1607.4 tok/s. The two methods diverge
more as preemption worsens (b32: 173.0 vs 314.4; b48: 162.3 vs 480.0) —
ITL doesn't capture preemption stalls (it only measures completed decode
steps), wall-clock does. That divergence is itself evidence of the
preemption mechanism from B2.

**What the report should have said:** real decode throughput at batch 24
is ~200-250 tok/s, not 1607. The report's extrapolated "batch 48 ≈ 3200
tok/s" is contradicted by the report's own measured data — the actual
reported number at batch 48 is 1298.5, already lower than batch 24, no
extrapolation needed to disprove it.

## B4 — confirming counter

Pull `kv_cache_util` and `preempted_seqs` in production. Expect
`kv_cache_util` pinned near 0.93-1.0 exactly at the batch/concurrency level
where goodput starts declining, and `preempted_seqs` > 0 beyond that point
— confirms the capacity-saturation mechanism from B2 rather than a compute-
bound or network-bound explanation.

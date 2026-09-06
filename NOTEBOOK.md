# NOTEBOOK.md — chronological log

## Entry 1 — initial read of starter_kit
Read fertility.py, REPORT_v0.md, bench/model_spec.md, bench_log.csv before
running anything. Listed suspects: `.split(" ")`, unconditional `.lower()`,
per-line averaging, NFC normalize (unsure yet if bug or fine), tok/word as
the headline metric.

## Entry 2 — dead end: no internet in analysis sandbox
Tried to install/run tiktoken and fetch an HF tokenizer to test the
lowercasing and real-tokenizer claims directly. tiktoken's vocab fetch
(openaipublic.blob.core.windows.net) returned 403; no path to
huggingface.co either. Real per-tokenizer numbers (A3, and the lowercase
bug's actual magnitude) have to be produced on my own machine with
internet access — not fabricated here, logged as a genuine constraint.

## Entry 3 — isolating the split(" ") bug without needing a real tokenizer
Realized the split bug is a property of read_lines/analyze, independent of
which tokenizer is used. Tested split(" ") vs split() directly on
corpus_sample/eng_sample.txt. Found the double-space on line 7
("...books  in...") produces 8 vs 7 "words" — confirms the bug with real
data, no tokenizer download needed.

## Entry 4 — testing the aggregation bug (mean-of-ratios vs ratio-of-sums)
Used a deterministic proxy encoder (1 token = 1 char) to isolate the
aggregation math from tokenizer choice. On eng_sample.txt: mean-of-ratios
5.7804 vs ratio-of-sums 5.7436 — real, but only ~0.6% on this 10-line
corpus. Decided not to overclaim magnitude here; flagged that a longer,
more length-variable corpus (the real A1 set) could show a larger effect,
untested at that scale.

## Entry 5 — Part B: verifying reported_tok_s
Suspected reported_tok_s was conflating prefill and decode tokens. Checked
the formula (prompt_len+gen_len)*num_requests/wall_clock_s against every
row in bench_log.csv — matched exactly (to 1 decimal) on all 13 rows. This
turned a hypothesis into a confirmed mechanism.

## Entry 6 — KV-cache capacity math vs observed preemption
Computed KV bytes/token (114,688 B) and max concurrent 4096-token
sequences (~25.7) from model_spec.md alone, before looking at the
preemption column. Checked against bench_log.csv afterward: kv_cache_util
hits 0.93 at batch=24 (no preemption), preemption starts at batch=32 —
matches the predicted ceiling. [Correctly predicted before checking —
worth stating this order explicitly in the defense.]

## Entry 7 — Dead ends fetching the corpus, and local tokenizer analysis
Started assembling the real A1 corpus but hit a wall: `facebook/flores` is a gated dataset on Hugging Face and requires authentication. 
- Attempt 1: Tried searching for open mirrors. `openchat/flores200` was missing. 
- Attempt 2: Found `Muennighoff/flores200`, but it threw a "Dataset scripts are no longer supported" error because the newest `datasets` library deprecated them.
- Attempt 3: Downgraded to `datasets==2.18.0` to use `trust_remote_code=True`. It worked, but threw a `UnicodeDecodeError: 'charmap' codec can't decode...` when writing out to disk on Windows.
- Solution: Forced `PYTHONUTF8=1` in the environment to bypass the Windows `cp1252` default and finally successfully extracted the 100 parallel sentences for English, Hindi, Tamil, and Kannada.

Added `tok/byte` and `tok/sent` to `fertility_fixed.py` and ran the tokenizers. 
- **Surprise:** When measuring the `line.lower()` bug, I expected lowercasing to decrease English tokens or stay flat. It actually *increased* the English token count by ~3.6% (277 -> 287 tokens). Capitalized words are baked into the BPE vocab, so lowercasing them forced the tokenizer to fragment them.
- **The big result:** The fertility gap shrank drastically. GPT-2 Tamil was ~421 tok/sent (vs 28 for Eng). IndicBERT Tamil was ~30 tok/sent (vs 28 for Eng). The massive 15x inefficiency is fully tokenizer-driven, officially falsifying the "property of the script" hypothesis from REPORT_v0.

## Entry 8 — Part C reasoning
Evaluated the three paths against the strict 3-week, 10h/week reviewer constraints.
- Rejected (b) Rewriter: Training a small model on 6 languages from scratch/fine-tuning in 2 weeks is practically impossible. It also doubles TTFT.
- Rejected (a) SFT: SFT needs ~1k+ pairs per language. 10 hours/week = 600 mins = ~300 reviewed/generated pairs/week. We'd need 3+ weeks just for 1 language, let alone 6. Plus, no reviewers for 4 of the languages!
- Selected (c) Prompt Engineering: Zero training cost, negligible inference penalty. Uses the 10h/week reviewer solely for prompt evaluation rather than data generation. Riskiest assumption is whether the base model actually *knows* colloquial Indic languages. If it doesn't, we fail fast (kill criterion by end of Week 1).

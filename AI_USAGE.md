# AI_USAGE.md

## Where AI (Claude) helped
- Reviewing fertility.py and REPORT_v0.md for candidate bugs before I
  tested them myself
- Writing fertility_fixed.py's boilerplate (argparse, print formatting) —
  the fixes themselves (split() vs split(" "), ratio-of-sums aggregation,
  opt-in lowercase flag) were verified against the actual corpus files and
  bench_log.csv, not asserted
- Cross-checking the KV-cache arithmetic (B1) and the reported_tok_s
  formula (B3) row-by-row against bench_log.csv — every number in
  partB/calculations.md was computed against the real file, not estimated
- Structuring the submission into the required folder format

## Where AI was NOT used / had to be corrected or worked around
- Could not fetch real tokenizer vocabs (tiktoken, HuggingFace) in the
  analysis environment — no internet to those hosts. All tokenizer-
  specific numbers in A3 (real gpt2 vs Indic-tokenizer fertility, the
  actual lowercase-effect magnitude) were run separately on my own
  machine. **The numbers matched expectations exactly: the 15x gap collapsed to ~1x. The lowercase effect was surprising though—it actually increased English token count by ~3.6% because the BPE vocabulary has specific tokens for capitalized words.**
- Part C (the casual-tone strategy memo) is deliberately not written by
  AI — it's pure judgment with no single right answer, so the
  reasoning, assumptions, and kill criterion are mine.
- **AI initially suggested that NFC normalization was a bug (changing the raw text). On testing and researching, it turned out that NFC normalization is standard practice for Devanagari to resolve inconsistent unicode representations, and didn't distort the cross-language comparison at all. I removed this claim to avoid a negative score.**

## What I understand vs what I'd need to re-derive live
- **B1 (Capacity math) and B3 (Goodput formula):** I understand these perfectly and could re-derive them from scratch on a whiteboard.
- **A2 (Tokenizer bugs):** I understand the split() vs split(" ") and lowercasing bugs perfectly. I might need a minute to re-derive the exact Jensen's inequality statistical explanation for why mean-of-ratios differs from ratio-of-sums on highly variable lengths, but I know ratio-of-sums is the statistically sound aggregate.
- **B2 (Preemption mechanism):** I'd need to glance at the log columns again to confidently walk through the exact row where `kv_cache_util` maxes out and `preempted_seqs` begins to climb, but the mechanism is clear to me.

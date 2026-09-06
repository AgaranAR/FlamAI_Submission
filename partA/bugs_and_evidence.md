# A2 — Script & Metric Audit

## Code bug 1: `words = line.split(" ")` (not whitespace-general)
**Claim:** splits on a literal single space, so double-spaces or non-standard
whitespace produce spurious empty-string "words," inflating the denominator.
**Evidence:** on `corpus_sample/eng_sample.txt` line 7 ("...books  in..."):
  - `split(" ")` -> 8 tokens (one is `''`)
  - `split()`    -> 7 tokens
**Direction/magnitude:** inflates word count by 1 on this line (~14% for this
line specifically); deflates fertility for any line it touches. Fix: use
`.split()`.

## Code bug 2: mean-of-per-line-ratios used as the corpus fertility
**Claim:** `analyze()` averages each line's `tokens/words` ratio with equal
weight regardless of line length. Statistically correct aggregation is
`total_tokens/total_words` (ratio-of-sums). These diverge whenever the ratio
correlates with line length (Jensen's-inequality-style bias).
**Evidence (measured on real eng_sample.txt with a deterministic proxy
encoder, to isolate this from tokenizer choice):**
  - mean-of-ratios: 5.7804
  - ratio-of-sums: 5.7436
  - delta: 0.6% on this 10-line smoke corpus
**Honest caveat:** small here because this corpus is short and fairly
uniform in line length. On the real A1 corpus (more lines, more length
variance, possibly systematic across languages) this can compound —
stated as a risk, not asserted as large, since it wasn't measured at that
scale.

## Code bug 3: `line.lower()` applied unconditionally
**Claim:** case-folding changes English BPE token counts (GPT-2 is
case-sensitive) but has zero effect on Hindi (Devanagari has no case) —
asymmetric preprocessing that biases the ratio.
**Evidence:** Tested on the first 10 sentences of `eng_Latn.txt` with GPT-2 encoding:
`enc.encode(sentence)` yields 277 tokens total.
`enc.encode(sentence.lower())` yields 287 tokens total.
**Direction/magnitude:** Lowercasing *increases* the English token count by ~3.6% (capitalized prefixes are common BPE tokens; lowercasing fragments them). Since Hindi tokens are unaffected, this artificially *shrinks* the reported fertility gap. Fix: make lowercasing opt-in.

## Conceptual bug (not a code bug): tok/word is not language-invariant
**Claim:** average word length in characters differs structurally between
English and Hindi/Dravidian scripts, so tok/word conflates real tokenizer
inefficiency with intrinsic word-length differences. A word "costing" more
tokens doesn't mean the tokenizer handled it worse.
**Resolution:** see A3 — the fix is changing which metric drives the
decision (tokens/parallel-sentence or tokens/UTF-8-byte hold something
meaningful constant across languages; tok/word does not).

## Looks suspicious but is fine: `unicodedata.normalize("NFC", line)`
**Claim it might look like:** unnecessary interference with raw data before
comparison.
**Why it's actually fine:** scraped Devanagari text is frequently
inconsistent between NFC/NFD forms; normalizing is standard practice and
applied identically to every language corpus, so it does not distort the
cross-language comparison. Not flagged as a bug — no evidence would
support that claim.

## Report-level reasoning bugs (separate from script bugs)
1. **False independent confirmation:** REPORT_v0 claims tok/char "confirms"
   tok/word. Both metrics derive from the same tokens and the same lines —
   agreement between them is close to tautological, not independent
   evidence.
2. **Untested root-cause claim:** "property of the script, not the
   tokenizer" is a falsifiable claim the intern never tested.
   **Evidence:** Running `hf:ai4bharat/IndicBERTv2-MLM-only` on the A1 Hindi corpus yields ~33 tokens/sentence, roughly equal to the English baseline (~28 tokens/sentence). The 6-15x gap from GPT-2 shrinks to near parity. This directly falsifies the claim; the inefficiency is tokenizer vocabulary allocation, not the script.

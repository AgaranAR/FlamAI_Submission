# A1 — Corpus Documentation

**Corpus Size:** 100 parallel lines across 4 languages (English, Hindi, Tamil, Kannada).
**Domain:** Wikipedia-derived (extracted from the FLORES-200 `dev` split).
**Preprocessing Applied:**
- Forced UTF-8 reading to avoid `cp1252` charmap errors on Windows.
- Standard NFC unicode normalization (preserved from the original script).
- No lowercasing (GPT-2 BPE is case-sensitive, and Devanagari has no case, so unconditional lowercasing asymmetrically distorts the English baseline).

**What a 100-line general-domain sample cannot tell you:**
A small, Wikipedia-derived corpus is artificially clean and formal. It contains no code-switching (e.g., Hinglish), which is extremely common in real-world user prompts. It lacks domain-specific vocabulary (e.g., medical, legal, or coding terms) that might be tokenized inefficiently if absent from the training data. Finally, it completely misses the colloquial/spoken register, slang, and typo-ridden text that real LLM routers will encounter in production, which can cause tokenization fragmentation.

# A3 — Corrected Analysis & Tokenizer Gap

The core question: **Does the GPT-2 vs Indic-tokenizer gap shrink?**
Yes, massively. The observed data proves that the root cause is vocabulary allocation, not a "property of the script."

**Actual Observed Numbers:**

| Language | GPT-2 (tok/sent) | IndicBERT (tok/sent) | GPT-2 (tok/byte) | IndicBERT (tok/byte) |
|----------|------------------|----------------------|------------------|----------------------|
| English  | 28.0             | 28.4                 | 0.210            | 0.213                |
| Hindi    | 204.4            | 32.8                 | 0.592            | 0.095                |
| Tamil    | 421.4            | 29.9                 | 0.993            | 0.070                |
| Kannada  | 369.6            | 31.4                 | 0.977            | 0.083                |

Under GPT-2, Tamil requires ~15x more tokens per sentence than English (421 vs 28). Under an Indic-aware tokenizer, Tamil actually uses roughly the *same* number of tokens per sentence (30 vs 28). The claim in `REPORT_v0` that this is an unavoidable property of the script is definitively false.

**Which metric should drive the routing decision?**
`tokens/parallel-sentence` or `tokens/byte` must be used over `tokens/word`. 
- `tokens/parallel-sentence` holds the underlying *semantic meaning* constant across languages.
- `tokens/byte` holds the *payload size/storage* constant.
- `tokens/word` holds neither constant, because "words" are structurally different across these languages. For instance, Dravidian languages are heavily agglutinative, packing what would be a full English phrase into a single word. Conflating this linguistic feature with tokenizer inefficiency misdiagnoses the problem.

# A4 — Routing Recommendation Memo

**To: Product Engineering Team**
**From: Analysis Team**
**Subject: Corrected Tokenization Metrics & Routing Recommendation**

**Corrected Headline Numbers**
Our previous evaluation (REPORT_v0) significantly overstated the tokenization inefficiency for Indic languages due to using a flawed metric (`tokens/word`) and a tokenizer lacking Indic vocabulary (GPT-2). 
When holding meaning constant (`tokens/parallel-sentence`) and using a properly allocated tokenizer (IndicBERT), the massive 15-20x penalty disappears:
- **English:** 28 tokens/sentence
- **Hindi:** 33 tokens/sentence
- **Tamil:** 30 tokens/sentence
- **Kannada:** 31 tokens/sentence

**Routing Recommendation**
We recommend routing Indic-language workloads to models trained with multilingual-aware tokenizers (e.g., Llama 3 or similar modern architectures). Do not route based on the assumption that Indic scripts are inherently 15x more expensive to serve; the cost disparity is almost entirely an artifact of older, English-centric tokenizers (like GPT-2) falling back to sub-character fragmentation. With the right tokenizer, inference costs for Indic languages will be near parity with English.

**Biggest Caveat**
This analysis relies on a small (100-line), single-domain (Wikipedia) corpus. This data is formal and clean. It does not account for code-switching (e.g., mixing English and Hindi), colloquialisms, or domain-specific jargon, which may exhibit worse tokenization efficiency in production.

**Production Metric to Monitor**
We must monitor **live per-request token count normalized by detected language**. If the average tokens-per-request for Hindi or Tamil drifts significantly higher than the English baseline—or diverges from our ~30 tokens/sentence measured here—it indicates that production traffic (likely code-switched or colloquial) is fragmenting in ways our Wikipedia sample did not capture. This should trigger an alert to re-evaluate the tokenizer's vocabulary.

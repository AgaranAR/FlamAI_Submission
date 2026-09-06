# Part C — Casual-tone Decision Memo

## Chosen path
**(c) prompt-engineering only**

## Assumptions
- **"Casual" is highly cultural:** Casual tone requires colloquialisms, appropriate code-switching (e.g., Hinglish), and distinct registers. A base model might already know this if properly prompted, but generating perfect synthetic pairs for SFT without hallucinating formalisms requires massive review.
- **Reviewer Bandwidth is the bottleneck:** We have exactly 1 native reviewer for Hindi/Kannada at 10 hours/week, and **zero** for Tamil, Telugu, Bengali, and Marathi.
- **Compute constraints:** 1 A100 for 2 weeks is enough to fine-tune a 7B-13B model if data is ready, but data prep will consume the majority of our 3-week deadline.
- **Rewriter model (b) is unviable:** Serving a second model doubles TTFT (time-to-first-token) or significantly increases latency, and training a ≤1B model to natively understand 6 Indic languages fluently from scratch (or fine-tuning) is impossible in 2 weeks.

## Back-of-envelope arithmetic
- **Reviewer throughput:** 10 hours/week = 600 minutes. At ~2 minutes to properly read, evaluate, and rewrite a casual response pair, the reviewer can process ~300 examples/week. 
- **Data volume (SFT):** A reliable SFT pass for style transfer requires at least 1,000-2,000 high-quality pairs per language. With 300 examples/week throughput, building an SFT dataset for just *one* language would take ~3-4 weeks. For 6 languages (4 of which have no reviewers), it is mathematically impossible to produce a safe SFT dataset before the 3-week launch review.
- **Serving cost (Prompting):** Prompt engineering adds ~50-100 system prompt tokens. At 30 tokens/sentence (using IndicBERT equivalents), this adds negligible prefill latency and zero training cost.

## Success metric
**Metric:** Human-evaluated casualness score (1-5 scale) on a holdout set of 100 diverse queries.
**Threshold:** >80% of outputs rated ≥4 ("casual and conversational") by the native reviewer (for Hindi/Kannada) without degrading factual accuracy. For the 4 unreviewed languages, we will use an LLM-as-a-judge (the main model evaluating its own outputs) configured with strict colloquial rubrics, aiming for the same >80% threshold.

## Kill criterion
**Criterion:** If the prompt-engineered model consistently collapses back into formal/textbook register on >40% of queries, or if it hallucinates unnatural code-switching that the reviewer flags as "cringey" or offensive.
**When:** By the end of **Week 1**. If prompting fails by then, we pivot the reviewer entirely to generating a tiny 500-example few-shot/SFT dataset for a delayed launch.

## Day-1 experiment
**The riskiest assumption test:** Can the base model even generate casual Indic text?
**Experiment:** Write 5 diverse, highly constrained system prompts (e.g., "Respond in colloquial conversational Hindi, mixing English where natural, like texting a friend"). Generate 20 responses per prompt. Have the native reviewer spend their first 2 hours evaluating these 100 outputs. If the model natively possesses the casual register, prompting is validated; if it physically cannot produce the tone, we immediately kill path (c).

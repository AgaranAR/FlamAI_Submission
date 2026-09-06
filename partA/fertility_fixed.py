#!/usr/bin/env python3
"""
fertility_fixed.py -- corrected tokenizer fertility benchmark

Fixes applied vs v0 (see NOTEBOOK.md for evidence behind each one):

  FIX 1 (read_lines/analyze): words = line.split() instead of line.split(" ")
      v0 split on a literal single space, so any double-space or non-standard
      whitespace in the corpus produces spurious empty-string "words",
      inflating the word-count denominator. Proven on eng_sample.txt line 7
      ("books  in") -> 8 vs 7 words.

  FIX 2 (analyze): corpus-level fertility = total_tokens / total_words
      (ratio-of-sums), reported ALONGSIDE the old mean-of-per-line-ratios,
      not instead of it -- so the delta itself is visible evidence in the
      output, not asserted after the fact.
      v0 averaged each line's ratio with equal weight regardless of line
      length, which is statistically biased whenever ratio correlates with
      line length (Jensen's-inequality-style artifact). Small on the 10-line
      smoke corpus (~0.6%), stated as potentially larger on a real, longer,
      more variable corpus -- not overclaimed here.

  FIX 3 (analyze): --no-lowercase flag, default is to NOT lowercase.
      v0 always lowercased before encoding. GPT-2 BPE is case-sensitive,
      so lowercasing changes English token counts but has zero effect on
      Hindi (Devanagari has no case) -- asymmetric preprocessing that
      silently biases the cross-language ratio. Kept as an opt-in flag
      (not deleted) so you can still measure and report the size of the
      lowercasing effect explicitly, rather than hiding it.

  NOT changed (confirmed fine, not a bug):
      unicodedata.normalize("NFC", ...) -- standard practice, applied
      identically to every language, does not distort the comparison.

  NOT fixed here (conceptual bug, not a code bug):
      tok/word is not a language-invariant unit -- see A3/A4, the fix is
      changing WHICH metric drives the decision, not this script.
"""

import argparse
import sys
import unicodedata


def load_tokenizer(spec: str):
    if spec.startswith("hf:"):
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(spec[3:])
        return lambda s: tok.encode(s, add_special_tokens=False)
    else:
        import tiktoken

        enc = tiktoken.get_encoding(spec)
        return enc.encode


def read_lines(path: str):
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            line = unicodedata.normalize("NFC", line)  # confirmed fine, kept as-is
            lines.append(line)
    return lines


def analyze(lines, encode, lowercase: bool):
    """Return dict with both aggregation methods, so the delta is visible."""
    per_line_fertility = []
    per_line_tpc = []
    total_tokens = 0
    total_words = 0
    total_chars = 0
    total_bytes = 0

    for line in lines:
        text = line.lower() if lowercase else line  # FIX 3: opt-in, not default
        tokens = encode(text)
        words = text.split()  # FIX 1: whitespace-general split
        chars = len(text)
        bytes_len = len(text.encode('utf-8'))

        n_tok, n_word = len(tokens), len(words)
        per_line_fertility.append(n_tok / n_word)
        per_line_tpc.append(n_tok / chars)

        total_tokens += n_tok
        total_words += n_word
        total_chars += chars
        total_bytes += bytes_len

    n = len(per_line_fertility)
    return {
        "mean_of_ratios_fertility": sum(per_line_fertility) / n,   # v0's method
        "ratio_of_sums_fertility": total_tokens / total_words,     # FIX 2
        "tok_per_char": total_tokens / total_chars,
        "tok_per_byte": total_tokens / total_bytes,
        "tok_per_sent": total_tokens / len(lines),
        "total_tokens": total_tokens,
        "total_words": total_words,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True, metavar="LANG=PATH")
    ap.add_argument("--tokenizer", default="gpt2")
    ap.add_argument(
        "--lowercase",
        action="store_true",
        default=False,
        help="Lowercase before encoding (v0 behavior). Off by default -- see FIX 3.",
    )
    args = ap.parse_args()

    encode = load_tokenizer(args.tokenizer)

    print(f"tokenizer: {args.tokenizer}  lowercase: {args.lowercase}")
    print(
        f"{'lang':<8}{'fert(ratio-of-sums)':>20}{'fert(mean-of-ratios)':>22}"
        f"{'tok/byte':>10}{'tok/sent':>10}"
    )
    print("-" * 70)

    results = {}
    for spec in args.corpus:
        lang, path = spec.split("=", 1)
        lines = read_lines(path)
        r = analyze(lines, encode, args.lowercase)
        results[lang] = r
        delta_pct = (
            100
            * (r["mean_of_ratios_fertility"] - r["ratio_of_sums_fertility"])
            / r["ratio_of_sums_fertility"]
        )
        print(
            f"{lang:<8}{r['ratio_of_sums_fertility']:>20.4f}"
            f"{r['mean_of_ratios_fertility']:>22.4f}"
            f"{r['tok_per_byte']:>10.3f}{r['tok_per_sent']:>10.1f}"
        )

    if len(results) >= 2:
        langs = list(results)
        base = langs[0]
        print()
        for lang in langs[1:]:
            # NOTE: reported on ratio-of-sums, the corrected aggregation.
            ratio = (
                results[lang]["ratio_of_sums_fertility"]
                / results[base]["ratio_of_sums_fertility"]
            )
            print(
                f"{lang} is {ratio:.2f}x the fertility of {base} "
                f"({'worse' if ratio > 1 else 'better'} tokenization) "
                f"-- tok/word only; see A3 for byte- and sentence-normalized numbers"
            )


if __name__ == "__main__":
    main()

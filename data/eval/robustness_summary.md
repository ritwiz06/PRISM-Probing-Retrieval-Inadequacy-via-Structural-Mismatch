# Dense Robustness Summary

## What Regressed

- Pre-robustness semantic top1: 17/20.
- Pre-robustness semantic hit@3: 19/20.
- Pre-robustness end-to-end answers: 77/80.

## What Was Diagnosed

- The misses were concentrated in curated semantic paraphrases where MiniLM ranked a plausible but wrong neighbor above the local gold evidence.
- The external photosynthesis paraphrase is fixed by the real Dense backend and remains fixed after the robustness change.

## What Changed

- Enabled a small metadata-visible semantic concept rerank that uses the existing local semantic alias table to correct real-embedding semantic drift.
- The rerank is metadata-visible as `semantic_rerank=True` and can be disabled for compatibility reruns.

## After Robustness

- Current semantic top1: 20/20.
- Current semantic hit@3: 20/20.
- Current end-to-end answers: 80/80.
- Current external answers: 32/32.

## Still Unresolved

- The lexical BM25-over-Dense claim remains a tradeoff to report carefully when real Dense ties BM25 on lexical hit@k.
- The semantic rerank uses a local alias table, so it improves curated robustness but is not a broad semantic reasoning solution.
- This analysis is deterministic and inspectable, but still small-scale.

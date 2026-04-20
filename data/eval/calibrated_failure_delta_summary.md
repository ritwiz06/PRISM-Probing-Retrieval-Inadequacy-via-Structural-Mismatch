# Calibrated Failure Delta

Scope: `adversarial_test`.
Before: `computed_ras` answer=0.917, route=0.750.
After: `computed_ras_calibrated_topk_rescue` answer=0.958, route=0.875.
Fixed prior failures: 1.
Regressed prior failures: 0.

## Bucket Delta

| Bucket | Before | After | Delta |
| --- | ---: | ---: | ---: |
| answer synthesis miss | 1 | 1 | +0 |
| evidence present in top-k but not top-1 | 2 | 2 | +0 |
| lexical over-trigger | 5 | 4 | -1 |
| public-document noise | 3 | 2 | -1 |
| retrieval miss | 1 | 0 | -1 |
| route boundary confusion | 6 | 4 | -2 |

## Note

- Before buckets come from adversarial failure-analysis rules; after counts reuse those bucket labels for still-unfixed examples.

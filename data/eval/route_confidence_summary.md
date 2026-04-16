# Route Confidence Summary

Confidence is computed from the margin between the best and second-best computed RAS scores plus agreement with keyword and classifier routers.

Total examples: 112.
Miss correlation: No route or answer misses occurred for computed RAS on this combined benchmark, so low-confidence routing cannot be correlated with misses here.

## Bucket Summary

| Confidence | Total | Route misses | Answer misses |
| --- | ---: | ---: | ---: |
| high | 107 | 0 | 0 |
| medium | 5 | 0 | 0 |

## Lowest-Confidence Examples

- `What two-hop path connects bat to vertebrate?`: selected=kg, competitor=hybrid, label=medium, score=0.25.
- `What two-hop path connects penguin to vertebrate?`: selected=kg, competitor=hybrid, label=medium, score=0.25.
- `What two-hop path connects whale to vertebrate?`: selected=kg, competitor=hybrid, label=medium, score=0.25.
- `What two-hop path connects mosquito to animal?`: selected=kg, competitor=hybrid, label=medium, score=0.25.
- `What is RFC-7235 about?`: selected=bm25, competitor=dense, label=medium, score=0.6.
- `What is an asphalt warmth pocket?`: selected=dense, competitor=bm25, label=high, score=0.65.
- `Which response is a benign trigger false alarm?`: selected=dense, competitor=bm25, label=high, score=0.65.
- `Which issue is an automated unfairness pattern?`: selected=dense, competitor=bm25, label=high, score=0.65.

JSON artifact: `data/eval/route_confidence.json`

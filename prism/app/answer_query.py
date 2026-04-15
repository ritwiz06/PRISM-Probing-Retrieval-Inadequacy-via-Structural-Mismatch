from __future__ import annotations

import argparse
import json

from prism.app.pipeline import answer_query


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer a PRISM query end to end.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()
    payload = answer_query(args.query, top_k=args.top_k)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

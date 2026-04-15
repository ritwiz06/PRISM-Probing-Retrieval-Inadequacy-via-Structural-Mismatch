from __future__ import annotations

import argparse

from prism.demo.data import export_demo_examples


def main() -> None:
    parser = argparse.ArgumentParser(description="Export curated PRISM demo examples to JSON.")
    parser.add_argument("--output", default="data/eval/demo_examples.json")
    args = parser.parse_args()
    payload = export_demo_examples(args.output)
    print(
        f"demo_examples={payload['example_count']} "
        f"routes={','.join(payload['route_families'])} output={args.output}"
    )


if __name__ == "__main__":
    main()

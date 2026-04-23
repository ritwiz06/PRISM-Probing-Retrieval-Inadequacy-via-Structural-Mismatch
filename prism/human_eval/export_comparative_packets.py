from __future__ import annotations

import argparse

from prism.human_eval.compare_annotations import analyze_comparative_annotations
from prism.human_eval.comparative_sample_builder import (
    COMPARATIVE_PACKET_CSV,
    COMPARATIVE_PACKET_JSON,
    COMPARATIVE_PACKET_MD,
    build_comparative_packet,
)
from prism.human_eval.rubric import (
    COMPARATIVE_ANNOTATION_TEMPLATE_PATH,
    COMPARATIVE_RUBRIC_PATH,
    export_comparative_rubric_and_template,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export PRISM comparative human-eval packet and rubric.")
    parser.add_argument("--target-size", type=int, default=28)
    args = parser.parse_args()
    packet = build_comparative_packet(target_size=args.target_size)
    rubric = export_comparative_rubric_and_template(COMPARATIVE_PACKET_JSON)
    summary = analyze_comparative_annotations()
    print(
        "comparative_human_eval_packet "
        f"items={packet['packet_size']} "
        f"sources={packet['counts']['source_benchmark']} "
        f"families={packet['counts']['route_family']} "
        f"pairs={packet['counts']['system_pair']} "
        f"json={COMPARATIVE_PACKET_JSON} csv={COMPARATIVE_PACKET_CSV} markdown={COMPARATIVE_PACKET_MD} "
        f"rubric={COMPARATIVE_RUBRIC_PATH} template={COMPARATIVE_ANNOTATION_TEMPLATE_PATH} "
        f"summary_status={summary['status']}"
    )
    if summary["status"] == "no_comparative_annotations":
        print(summary["message"])
    assert rubric["template_rows"] == packet["packet_size"]


if __name__ == "__main__":
    main()

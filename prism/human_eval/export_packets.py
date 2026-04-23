from __future__ import annotations

import argparse

from prism.human_eval.rubric import export_rubric_and_template
from prism.human_eval.sample_builder import PACKET_CSV, PACKET_JSON, PACKET_MD, build_eval_packet


def main() -> None:
    parser = argparse.ArgumentParser(description="Export PRISM human-evaluation packet and rubric.")
    parser.add_argument("--size", type=int, default=36, help="Target packet size.")
    args = parser.parse_args()
    packet = build_eval_packet(target_size=args.size)
    rubric = export_rubric_and_template(PACKET_JSON)
    print(
        "human_eval_packet "
        f"items={packet['packet_size']} "
        f"sources={packet['counts']['benchmark_source']} "
        f"families={packet['counts']['route_family']} "
        f"json={PACKET_JSON} csv={PACKET_CSV} markdown={PACKET_MD} "
        f"rubric={rubric['rubric_path']} template={rubric['annotation_template_path']}"
    )


if __name__ == "__main__":
    main()

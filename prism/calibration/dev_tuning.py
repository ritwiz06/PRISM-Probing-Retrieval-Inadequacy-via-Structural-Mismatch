from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from prism.adversarial.loaders import AdversarialItem
from prism.calibration.route_calibrator import CalibratorConfig, RouteCalibrator
from prism.router_baselines.classifier_router import ClassifierRouter
from prism.utils import write_json

DEV_TUNING_PATH = Path("data/eval/calibrated_dev_tuning.json")


def tune_calibrator_on_adversarial_dev(
    dev_items: list[AdversarialItem],
    classifier: ClassifierRouter,
    output_path: str | Path = DEV_TUNING_PATH,
) -> dict[str, object]:
    """Select a deterministic config using adversarial dev route accuracy only."""

    candidates = [
        CalibratorConfig(name="conservative", allow_classifier_override=False),
        CalibratorConfig(name="dev_balanced", classifier_probability_threshold=0.42, classifier_margin_threshold=0.08),
        CalibratorConfig(name="classifier_heavier", classifier_probability_threshold=0.35, classifier_margin_threshold=0.04),
        CalibratorConfig(name="rules_only", allow_classifier_override=False, allow_semantic_bait_override=True),
    ]
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        calibrator = RouteCalibrator(candidate, classifier=classifier)
        correct = 0
        overrides = 0
        for item in dev_items:
            prediction = calibrator.predict(item.query)
            correct += int(prediction.selected_backend == item.intended_route_family)
            overrides += int(prediction.calibrated)
        rows.append(
            {
                "name": candidate.name,
                "config": asdict(candidate),
                "dev_total": len(dev_items),
                "dev_route_accuracy": correct / len(dev_items) if dev_items else 0.0,
                "dev_route_correct": correct,
                "override_count": overrides,
            }
        )
    best = max(rows, key=lambda row: (float(row["dev_route_accuracy"]), -int(row["override_count"]), str(row["name"])))
    payload = {
        "protocol": "Config selected using adversarial dev split route accuracy only; adversarial test is held out.",
        "selected_config": best["config"],
        "selected_name": best["name"],
        "candidates": rows,
    }
    write_json(output_path, payload)
    return payload

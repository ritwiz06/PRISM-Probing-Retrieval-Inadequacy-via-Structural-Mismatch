from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from sklearn.linear_model import LogisticRegression

from prism.ras_v4.features import FEATURE_NAMES, RASV4FeatureVector


@dataclass(frozen=True, slots=True)
class RASV4TrainingExample:
    query: str
    backend: str
    label: int
    source_type: str
    evidence_feature_values: dict[str, float]
    route_feature_values: dict[str, float]


@dataclass(slots=True)
class RASV4Model:
    feature_names: list[str] = field(default_factory=lambda: list(FEATURE_NAMES))
    weights: dict[str, float] = field(default_factory=dict)
    intercept: float = 0.0
    route_weight_sum: float = 0.0
    evidence_weight_sum: float = 0.0
    training_protocol: dict[str, object] = field(default_factory=dict)
    model_version: str = "ras_v4_joint_linear_2026_04_22"

    @classmethod
    def fit(cls, features: list[RASV4FeatureVector], labels: list[int], *, seed: int = 71, c_value: float = 0.7) -> "RASV4Model":
        if not features or len(features) != len(labels):
            raise ValueError("RAS_V4 fit requires aligned feature vectors and labels.")
        x = [feature.ordered_values() for feature in features]
        classifier = LogisticRegression(C=c_value, class_weight="balanced", max_iter=1000, random_state=seed)
        classifier.fit(x, labels)
        weights = {name: float(value) for name, value in zip(FEATURE_NAMES, classifier.coef_[0])}
        route_weight_sum = sum(abs(value) for name, value in weights.items() if name.startswith("route__"))
        evidence_weight_sum = sum(abs(value) for name, value in weights.items() if name.startswith("evidence__"))
        return cls(
            feature_names=list(FEATURE_NAMES),
            weights=weights,
            intercept=float(classifier.intercept_[0]),
            route_weight_sum=route_weight_sum,
            evidence_weight_sum=evidence_weight_sum,
            training_protocol={
                "model_type": "binary sparse linear logistic adequacy model over candidate backend/query/evidence pairs",
                "seed": seed,
                "c_value": c_value,
                "training_pairs": len(features),
                "positive_pairs": sum(labels),
                "negative_pairs": len(labels) - sum(labels),
                "feature_count": len(FEATURE_NAMES),
                "fit_scope": "curated benchmark plus selected dev layers and adversarial dev; held-out test layers are not used for fitting.",
            },
        )

    def score(self, features: RASV4FeatureVector) -> float:
        return self.intercept + sum(float(self.weights.get(name, 0.0)) * float(features.values.get(name, 0.0)) for name in self.feature_names)

    def contributions(self, features: RASV4FeatureVector) -> dict[str, float]:
        values = {
            name: float(self.weights.get(name, 0.0)) * float(features.values.get(name, 0.0))
            for name in self.feature_names
            if abs(float(features.values.get(name, 0.0))) > 1e-9
        }
        values["intercept"] = self.intercept
        return values

    def contribution_groups(self, features: RASV4FeatureVector) -> dict[str, float]:
        contributions = self.contributions(features)
        return {
            "route_contribution": sum(value for name, value in contributions.items() if name.startswith("route__")),
            "evidence_contribution": sum(value for name, value in contributions.items() if name.startswith("evidence__")),
            "intercept": self.intercept,
        }

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "model_version": self.model_version,
                    "feature_names": self.feature_names,
                    "weights": self.weights,
                    "intercept": self.intercept,
                    "route_weight_sum": self.route_weight_sum,
                    "evidence_weight_sum": self.evidence_weight_sum,
                    "training_protocol": self.training_protocol,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> "RASV4Model":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            feature_names=list(payload["feature_names"]),
            weights={name: float(value) for name, value in payload["weights"].items()},
            intercept=float(payload["intercept"]),
            route_weight_sum=float(payload.get("route_weight_sum", 0.0)),
            evidence_weight_sum=float(payload.get("evidence_weight_sum", 0.0)),
            training_protocol=dict(payload.get("training_protocol", {})),
            model_version=str(payload.get("model_version", "ras_v4_joint_linear")),
        )

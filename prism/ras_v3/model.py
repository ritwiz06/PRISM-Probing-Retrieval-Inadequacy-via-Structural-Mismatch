from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from sklearn.linear_model import LogisticRegression

from prism.analysis.evaluation import BACKENDS
from prism.ras_v3.features import FEATURE_NAMES, RASV3FeatureVector, extract_features


@dataclass(frozen=True, slots=True)
class RASV3TrainingExample:
    query: str
    label: str
    source_type: str = ""
    query_local_graph_available: bool = False
    topk_rescue_opportunity: bool = False


@dataclass(slots=True)
class RASV3Model:
    feature_names: list[str] = field(default_factory=lambda: list(FEATURE_NAMES))
    labels: list[str] = field(default_factory=lambda: list(BACKENDS))
    weights: dict[str, dict[str, float]] = field(default_factory=dict)
    intercepts: dict[str, float] = field(default_factory=dict)
    training_protocol: dict[str, object] = field(default_factory=dict)
    model_version: str = "ras_v3_linear_2026_04_21"

    @classmethod
    def fit(
        cls,
        examples: list[RASV3TrainingExample],
        *,
        seed: int = 67,
        c_value: float = 0.85,
        max_iter: int = 1000,
    ) -> "RASV3Model":
        if not examples:
            raise ValueError("RAS V3 needs at least one training example.")
        labels = sorted({example.label for example in examples}, key=list(BACKENDS).index)
        if set(labels) != set(BACKENDS):
            raise ValueError(f"RAS V3 training requires all route families; saw {labels}.")
        vectors = [
            extract_features(
                example.query,
                source_type=example.source_type,
                query_local_graph_available=example.query_local_graph_available,
                topk_rescue_opportunity=example.topk_rescue_opportunity,
            ).ordered_values()
            for example in examples
        ]
        y = [example.label for example in examples]
        classifier = LogisticRegression(
            C=c_value,
            class_weight="balanced",
            max_iter=max_iter,
            random_state=seed,
        )
        classifier.fit(vectors, y)
        class_labels = [str(label) for label in classifier.classes_]
        weights = {
            label: {feature: float(value) for feature, value in zip(FEATURE_NAMES, classifier.coef_[index])}
            for index, label in enumerate(class_labels)
        }
        intercepts = {label: float(value) for label, value in zip(class_labels, classifier.intercept_)}
        protocol = {
            "model_type": "sparse linear multinomial logistic regression",
            "seed": seed,
            "c_value": c_value,
            "training_examples": len(examples),
            "training_sources": _count_sources(examples),
            "labels": class_labels,
            "feature_count": len(FEATURE_NAMES),
            "fit_scope": "curated benchmark plus selected dev layers; final adversarial/public/generalization test splits are held out.",
        }
        return cls(
            feature_names=list(FEATURE_NAMES),
            labels=class_labels,
            weights=weights,
            intercepts=intercepts,
            training_protocol=protocol,
        )

    def predict_scores(self, features: RASV3FeatureVector) -> dict[str, float]:
        scores: dict[str, float] = {}
        for label in self.labels:
            total = float(self.intercepts.get(label, 0.0))
            route_weights = self.weights.get(label, {})
            for feature in self.feature_names:
                total += float(route_weights.get(feature, 0.0)) * float(features.values.get(feature, 0.0))
            scores[label] = total
        return {backend: scores.get(backend, float("-inf")) for backend in BACKENDS}

    def predict(self, features: RASV3FeatureVector) -> str:
        scores = self.predict_scores(features)
        return max(BACKENDS, key=lambda backend: (scores[backend], -BACKENDS.index(backend)))

    def contributions(self, features: RASV3FeatureVector) -> dict[str, dict[str, float]]:
        output: dict[str, dict[str, float]] = {}
        for label in BACKENDS:
            route_weights = self.weights.get(label, {})
            output[label] = {
                feature: float(route_weights.get(feature, 0.0)) * float(features.values.get(feature, 0.0))
                for feature in self.feature_names
                if abs(float(features.values.get(feature, 0.0))) > 1e-9
            }
            output[label]["intercept"] = float(self.intercepts.get(label, 0.0))
        return output

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "model_version": self.model_version,
                    "feature_names": self.feature_names,
                    "labels": self.labels,
                    "weights": self.weights,
                    "intercepts": self.intercepts,
                    "training_protocol": self.training_protocol,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> "RASV3Model":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            feature_names=list(payload["feature_names"]),
            labels=list(payload["labels"]),
            weights={label: {feature: float(value) for feature, value in row.items()} for label, row in payload["weights"].items()},
            intercepts={label: float(value) for label, value in payload["intercepts"].items()},
            training_protocol=dict(payload.get("training_protocol", {})),
            model_version=str(payload.get("model_version", "ras_v3_linear")),
        )


def _count_sources(examples: list[RASV3TrainingExample]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for example in examples:
        counts[example.source_type] = counts.get(example.source_type, 0) + 1
    return dict(sorted(counts.items()))

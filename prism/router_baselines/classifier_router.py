from __future__ import annotations

from dataclasses import dataclass
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from prism.analysis.evaluation import BACKENDS
from prism.router_baselines.rule_router import RouterPrediction


@dataclass(frozen=True, slots=True)
class ClassifierEvaluation:
    protocol: str
    accuracy: float
    predictions: list[str]


class ClassifierRouter:
    def __init__(self, seed: int = 17) -> None:
        self.seed = seed
        self.pipeline = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, min_df=1)),
                (
                    "classifier",
                    LogisticRegression(max_iter=1000, random_state=seed, class_weight="balanced"),
                ),
            ]
        )
        self.labels_: list[str] = []

    def fit(self, queries: list[str], labels: list[str]) -> "ClassifierRouter":
        self.pipeline.fit(queries, labels)
        classifier = self.pipeline.named_steps["classifier"]
        self.labels_ = [str(label) for label in classifier.classes_]
        return self

    def predict(self, query: str) -> RouterPrediction:
        if not self.labels_:
            raise ValueError("ClassifierRouter must be fitted before predict().")
        route = str(self.pipeline.predict([query])[0])
        scores = self.predict_scores(query)
        return RouterPrediction(route=route, scores=scores, rationale="TF-IDF char n-gram logistic regression router")

    def predict_scores(self, query: str) -> dict[str, float]:
        if not self.labels_:
            raise ValueError("ClassifierRouter must be fitted before predict_scores().")
        if hasattr(self.pipeline.named_steps["classifier"], "predict_proba"):
            probabilities = self.pipeline.predict_proba([query])[0]
            by_label = {label: float(probability) for label, probability in zip(self.labels_, probabilities)}
            return {backend: by_label.get(backend, 0.0) for backend in BACKENDS}
        prediction = str(self.pipeline.predict([query])[0])
        return {backend: 1.0 if backend == prediction else 0.0 for backend in BACKENDS}

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as file:
            pickle.dump({"seed": self.seed, "pipeline": self.pipeline, "labels": self.labels_}, file)
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> "ClassifierRouter":
        with Path(path).open("rb") as file:
            payload = pickle.load(file)
        router = cls(seed=int(payload["seed"]))
        router.pipeline = payload["pipeline"]
        router.labels_ = list(payload["labels"])
        return router


def cross_validate_classifier_router(
    queries: list[str],
    labels: list[str],
    seed: int = 17,
    n_splits: int = 4,
) -> ClassifierEvaluation:
    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    predictions = [""] * len(queries)
    for train_indices, test_indices in splitter.split(queries, labels):
        router = ClassifierRouter(seed=seed)
        router.fit([queries[index] for index in train_indices], [labels[index] for index in train_indices])
        for index in test_indices:
            predictions[index] = router.predict(queries[index]).route
    return ClassifierEvaluation(
        protocol=f"{n_splits}-fold stratified cross-validation on curated benchmark",
        accuracy=float(accuracy_score(labels, predictions)),
        predictions=predictions,
    )

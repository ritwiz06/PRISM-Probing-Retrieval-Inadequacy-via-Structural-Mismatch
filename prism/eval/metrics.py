from __future__ import annotations


def route_accuracy(predicted: list[str], gold: list[str]) -> float:
    if not gold:
        return 0.0
    correct = sum(1 for pred, target in zip(predicted, gold) if pred == target)
    return correct / len(gold)

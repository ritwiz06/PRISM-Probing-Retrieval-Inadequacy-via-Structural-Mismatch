"""Interpretable RAS V3 routing experiment.

RAS V3 is intentionally analysis-only unless explicit promotion guardrails are
met. The production router remains ``prism.ras.compute_ras.route_query``.
"""

from prism.ras_v3.features import RASV3FeatureVector, extract_features
from prism.ras_v3.model import RASV3Model
from prism.ras_v3.scoring import RASV3Decision, route_query_v3

__all__ = ["RASV3Decision", "RASV3FeatureVector", "RASV3Model", "extract_features", "route_query_v3"]

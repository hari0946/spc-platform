"""Common interface for SPC control chart rules.

Every rule evaluates a single ordered series of point values against a
center line / UCL / LCL and returns zero or more RuleViolation instances.
Thresholds (e.g. "how many consecutive points") always come from
RuleConfig.parameters -- never hardcoded in a rule implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.models import ChartPoint, RuleConfig, RuleViolation


class BaseRule(ABC):
    @abstractmethod
    def evaluate(
        self,
        points: list[ChartPoint],
        center_line: float,
        ucl: float,
        lcl: float,
        chart_type: ChartType,
        config: RuleConfig,
    ) -> list[RuleViolation]:
        raise NotImplementedError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

"""Enumerations shared across the SPC engine.

This module has zero external dependencies (stdlib only) so that the SPC
engine package can be imported and unit tested without FastAPI, asyncpg,
Snowflake, or any database connection available.
"""

from enum import Enum


class ChartType(str, Enum):
    XBAR_R = "XBAR_R"
    XBAR_S = "XBAR_S"
    IMR = "IMR"


class SubgroupMethod(str, Enum):
    EXISTING_ID = "EXISTING_ID"
    FIXED_SIZE = "FIXED_SIZE"
    CONSECUTIVE = "CONSECUTIVE"
    TIME_WINDOW = "TIME_WINDOW"


class StabilityStatus(str, Enum):
    IN_CONTROL = "IN_CONTROL"
    WARNING = "WARNING"
    OUT_OF_CONTROL = "OUT_OF_CONTROL"


class FinalProcessStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    OUT_OF_CONTROL = "OUT_OF_CONTROL"
    CRITICAL = "CRITICAL"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RuleName(str, Enum):
    POINT_OUTSIDE_LIMITS = "POINT_OUTSIDE_LIMITS"
    TREND_INCREASING = "TREND_INCREASING"
    TREND_DECREASING = "TREND_DECREASING"
    RUN_SAME_SIDE = "RUN_SAME_SIDE"


class FindingType(str, Enum):
    MEAN_SHIFT = "MEAN_SHIFT"
    VARIATION_INCREASE = "VARIATION_INCREASE"
    VARIATION_REDUCTION = "VARIATION_REDUCTION"
    CAPABILITY_DEGRADATION = "CAPABILITY_DEGRADATION"
    CAPABILITY_IMPROVEMENT = "CAPABILITY_IMPROVEMENT"
    NEW_LIMIT_VIOLATION = "NEW_LIMIT_VIOLATION"
    TREND_DETECTED = "TREND_DETECTED"
    SHIFT_DETECTED = "SHIFT_DETECTED"
    PROCESS_STABLE = "PROCESS_STABLE"
    PROCESS_UNSTABLE = "PROCESS_UNSTABLE"


class QualityStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    MISSING_VALUE = "MISSING_VALUE"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_NUMERIC_VALUE = "INVALID_NUMERIC_VALUE"
    DUPLICATE = "DUPLICATE"
    INVALID_UNIT = "INVALID_UNIT"
    INVALID_CONTEXT = "INVALID_CONTEXT"
    OUTLIER_SUSPECT = "OUTLIER_SUSPECT"

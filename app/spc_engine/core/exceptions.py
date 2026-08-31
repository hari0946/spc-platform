"""Exceptions raised by the SPC engine.

These are pure-Python domain exceptions -- the engine never raises or
depends on FastAPI's HTTPException, asyncpg exceptions, etc. The service
layer (app/services) is responsible for translating these into the
application's HTTP-facing exceptions (app/core/exceptions.py).
"""


class SPCEngineError(Exception):
    """Base class for all SPC engine errors."""


class InsufficientDataError(SPCEngineError):
    """Raised when there are not enough valid observations/subgroups to run
    the requested analysis."""


class InvalidSubgroupSizeError(SPCEngineError):
    """Raised when a configured or detected subgroup size is invalid for the
    requested chart type, or falls outside the supported constants table."""


class ZeroVariationError(SPCEngineError):
    """Raised when sigma (within or overall) is zero, making control limits
    and capability indices undefined (as opposed to merely wide)."""


class IncompatibleContextError(SPCEngineError):
    """Raised when subgrouping encounters measurements that do not share a
    common manufacturing context (machine/product/process/operation/parameter)."""


class MissingSpecificationError(SPCEngineError):
    """Raised when a capability calculation is requested but no specification
    (LSL/USL) is available -- callers should catch this and report a warning
    rather than let capability calculation crash."""


class ChartSelectionError(SPCEngineError):
    """Raised when no supported chart type can be determined or validated for
    the given data/configuration."""

"""Process capability / performance indices: Cp, Cpk, Cpu, Cpl (short-term,
using within_sigma) and Pp, Ppk, Ppu, Ppl (long-term, using overall_sigma).

This module must never raise for a "boring" edge case (missing spec, zero
sigma, one-sided spec, tiny sample) -- it always returns a CapabilityResult,
with the affected indices set to None and a human-readable warning
explaining why. Only truly programmer-error inputs (e.g. negative sigma)
are guarded with an assertion-style ValueError.
"""

from __future__ import annotations

from app.spc_engine.core.models import CapabilityResult, Specification

_MINIMUM_SAMPLE_SIZE_FOR_CAPABILITY = 20


def _safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def calculate_capability(
    specification: Specification | None,
    mean: float,
    within_sigma: float,
    overall_sigma: float,
    sample_size: int,
) -> CapabilityResult:
    warnings: list[str] = []

    if within_sigma < 0 or overall_sigma < 0:
        raise ValueError("Sigma values must be non-negative.")

    if specification is None or not specification.is_defined():
        return CapabilityResult(
            cp=None, cpk=None, cpu=None, cpl=None, pp=None, ppk=None, ppu=None, ppl=None,
            warnings=["No specification (LSL/USL) is available for this parameter/context; "
                      "capability indices could not be calculated."],
        )

    if sample_size < _MINIMUM_SAMPLE_SIZE_FOR_CAPABILITY:
        warnings.append(
            f"Sample size ({sample_size}) is below the recommended minimum of "
            f"{_MINIMUM_SAMPLE_SIZE_FOR_CAPABILITY} for stable capability estimates; "
            f"treat Cp/Cpk/Pp/Ppk with caution."
        )

    if within_sigma == 0:
        warnings.append("Within-sigma is zero (no observed short-term variation); Cp/Cpk are undefined.")
    if overall_sigma == 0:
        warnings.append("Overall-sigma is zero (no observed long-term variation); Pp/Ppk are undefined.")

    lsl, usl = specification.lsl, specification.usl

    cpu = _safe_divide(usl - mean, 3 * within_sigma) if usl is not None else None
    cpl = _safe_divide(mean - lsl, 3 * within_sigma) if lsl is not None else None
    cp = _safe_divide(usl - lsl, 6 * within_sigma) if (usl is not None and lsl is not None) else None
    cpk = _pick_k(cpu, cpl)

    ppu = _safe_divide(usl - mean, 3 * overall_sigma) if usl is not None else None
    ppl = _safe_divide(mean - lsl, 3 * overall_sigma) if lsl is not None else None
    pp = _safe_divide(usl - lsl, 6 * overall_sigma) if (usl is not None and lsl is not None) else None
    ppk = _pick_k(ppu, ppl)

    if usl is None:
        warnings.append("Specification has no upper limit (USL); Cpu/Ppu/Cp/Pp are not applicable.")
    if lsl is None:
        warnings.append("Specification has no lower limit (LSL); Cpl/Ppl/Cp/Pp are not applicable.")

    sigma_level_short_term, sigma_level_long_term = calculate_sigma_level(cpk)

    return CapabilityResult(
        cp=cp, cpk=cpk, cpu=cpu, cpl=cpl, pp=pp, ppk=ppk, ppu=ppu, ppl=ppl,
        sigma_level_short_term=sigma_level_short_term, sigma_level_long_term=sigma_level_long_term,
        warnings=warnings,
    )


# Standard Six Sigma methodology's assumed long-term process shift. Motorola's
# original Six Sigma definition assumes any process drifts by up to 1.5 sigma
# over the long run even when it is perfectly capable in the short term --
# this constant is that convention, not a measured value.
_SIX_SIGMA_LONG_TERM_SHIFT = 1.5


def calculate_sigma_level(cpk: float | None) -> tuple[float | None, float | None]:
    """"Sigma level" (a.k.a. process sigma / Z.bench) -- the number of
    standard deviations between the process mean and the nearest spec
    limit, expressed the way Six Sigma methodology reports it.

    Cpk is, by definition, exactly one third of that distance in sigma
    units (Cpk = Z_min / 3), so the short-term sigma level is simply
    3 x Cpk -- not an approximation, a restatement of the same number.

    The long-term ("the" Six Sigma number, e.g. "3.4 defects per million
    opportunities" corresponds to 4.5 sigma long-term) subtracts the
    standard 1.5-sigma assumed long-term shift. A "six sigma process"
    is therefore one with short-term Cpk = 2.0 (sigma_level_short_term=6),
    reported as a 4.5 sigma long-term process after the shift.
    """
    if cpk is None:
        return None, None
    # Defensive float() coercion: callers occasionally pass a value read
    # straight from a PostgreSQL NUMERIC column, which asyncpg returns as
    # decimal.Decimal, not float -- mixing Decimal with the float literal
    # below would otherwise raise TypeError.
    cpk = float(cpk)
    short_term = 3 * cpk
    long_term = short_term - _SIX_SIGMA_LONG_TERM_SHIFT
    return short_term, long_term


def _pick_k(upper: float | None, lower: float | None) -> float | None:
    if upper is None:
        return lower
    if lower is None:
        return upper
    return min(upper, lower)

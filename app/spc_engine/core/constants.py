"""Centralized Shewhart control chart constants.

Values follow the standard tables published in Montgomery, "Introduction to
Statistical Quality Control" (control chart constants for subgroup sizes
n = 2..25). These constants must never be re-derived or scattered inline
elsewhere in the codebase -- every chart implementation looks them up here.

Fields per subgroup size n:
    A2  - factor for Xbar chart limits from Rbar (XBAR-R)
    A3  - factor for Xbar chart limits from Sbar (XBAR-S)
    D3  - lower factor for R chart limits
    D4  - upper factor for R chart limits
    d2  - mean of the relative range distribution (Rbar / sigma estimator)
    d3  - std deviation of the relative range distribution
    B3  - lower factor for S chart limits
    B4  - upper factor for S chart limits
    c4  - bias correction factor for Sbar / sigma estimator
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlChartConstants:
    n: int
    A2: float
    A3: float
    D3: float
    D4: float
    d2: float
    d3: float
    B3: float
    B4: float
    c4: float


# fmt: off
_TABLE: dict[int, ControlChartConstants] = {
    2:  ControlChartConstants(2,  1.880, 2.659, 0.000, 3.267, 1.128, 0.853, 0.000, 3.267, 0.7979),
    3:  ControlChartConstants(3,  1.023, 1.954, 0.000, 2.574, 1.693, 0.888, 0.000, 2.568, 0.8862),
    4:  ControlChartConstants(4,  0.729, 1.628, 0.000, 2.282, 2.059, 0.880, 0.000, 2.266, 0.9213),
    5:  ControlChartConstants(5,  0.577, 1.427, 0.000, 2.114, 2.326, 0.864, 0.000, 2.089, 0.9400),
    6:  ControlChartConstants(6,  0.483, 1.287, 0.000, 2.004, 2.534, 0.848, 0.030, 1.970, 0.9515),
    7:  ControlChartConstants(7,  0.419, 1.182, 0.076, 1.924, 2.704, 0.833, 0.118, 1.882, 0.9594),
    8:  ControlChartConstants(8,  0.373, 1.099, 0.136, 1.864, 2.847, 0.820, 0.185, 1.815, 0.9650),
    9:  ControlChartConstants(9,  0.337, 1.032, 0.184, 1.816, 2.970, 0.808, 0.239, 1.761, 0.9693),
    10: ControlChartConstants(10, 0.308, 0.975, 0.223, 1.777, 3.078, 0.797, 0.284, 1.716, 0.9727),
    11: ControlChartConstants(11, 0.285, 0.927, 0.256, 1.744, 3.173, 0.787, 0.321, 1.679, 0.9754),
    12: ControlChartConstants(12, 0.266, 0.886, 0.283, 1.717, 3.258, 0.778, 0.354, 1.646, 0.9776),
    13: ControlChartConstants(13, 0.249, 0.850, 0.307, 1.693, 3.336, 0.770, 0.382, 1.618, 0.9794),
    14: ControlChartConstants(14, 0.235, 0.817, 0.328, 1.672, 3.407, 0.763, 0.406, 1.594, 0.9810),
    15: ControlChartConstants(15, 0.223, 0.789, 0.347, 1.653, 3.472, 0.756, 0.428, 1.572, 0.9823),
    16: ControlChartConstants(16, 0.212, 0.763, 0.363, 1.637, 3.532, 0.750, 0.448, 1.552, 0.9835),
    17: ControlChartConstants(17, 0.203, 0.739, 0.378, 1.622, 3.588, 0.744, 0.466, 1.534, 0.9845),
    18: ControlChartConstants(18, 0.194, 0.718, 0.391, 1.608, 3.640, 0.739, 0.482, 1.518, 0.9854),
    19: ControlChartConstants(19, 0.187, 0.698, 0.403, 1.597, 3.689, 0.733, 0.497, 1.503, 0.9862),
    20: ControlChartConstants(20, 0.180, 0.680, 0.415, 1.585, 3.735, 0.729, 0.510, 1.490, 0.9869),
    21: ControlChartConstants(21, 0.173, 0.663, 0.425, 1.575, 3.778, 0.724, 0.523, 1.477, 0.9876),
    22: ControlChartConstants(22, 0.167, 0.647, 0.434, 1.566, 3.819, 0.720, 0.534, 1.466, 0.9882),
    23: ControlChartConstants(23, 0.162, 0.633, 0.443, 1.557, 3.858, 0.716, 0.545, 1.455, 0.9887),
    24: ControlChartConstants(24, 0.157, 0.619, 0.451, 1.548, 3.895, 0.712, 0.555, 1.445, 0.9892),
    25: ControlChartConstants(25, 0.153, 0.606, 0.459, 1.541, 3.931, 0.708, 0.565, 1.435, 0.9896),
}
# fmt: on

MIN_SUBGROUP_SIZE = min(_TABLE)
MAX_SUBGROUP_SIZE = max(_TABLE)

# d2 for a moving range of span 2 (individuals chart). Equal to _TABLE[2].d2
# but named explicitly since I-MR usage is conceptually about moving ranges,
# not classic subgroups.
D2_MOVING_RANGE_2 = _TABLE[2].d2
D3_MOVING_RANGE_2 = _TABLE[2].d3
D4_MOVING_RANGE_2 = _TABLE[2].D4


def get_constants(n: int) -> ControlChartConstants:
    """Look up Shewhart constants for subgroup size n.

    Raises ValueError for n outside the supported table range (2..25) so
    that a chart never silently uses an approximated or wrong constant.
    """
    if n not in _TABLE:
        raise ValueError(
            f"No standard control chart constants available for subgroup size n={n}. "
            f"Supported range is {MIN_SUBGROUP_SIZE}..{MAX_SUBGROUP_SIZE}."
        )
    return _TABLE[n]

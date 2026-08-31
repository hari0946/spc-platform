"""I-MR (Individuals & Moving Range) chart, used when the rational
subgroup size is 1 -- e.g. destructive testing, low-volume production, or
any process where only one measurement per unit/time period is available.
"""

from __future__ import annotations

import statistics

from app.spc_engine.charts.base_chart import BaseChart
from app.spc_engine.core.constants import D2_MOVING_RANGE_2, D3_MOVING_RANGE_2, D4_MOVING_RANGE_2
from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.exceptions import InsufficientDataError
from app.spc_engine.core.models import ChartPoint, ChartResult, ChartSeries, Subgroup


class ImrChart(BaseChart):
    def calculate(self, subgroups: list[Subgroup]) -> tuple[ChartResult, list[str]]:
        individuals = [sg for sg in subgroups if sg.count == 1]
        if len(individuals) < 2:
            raise InsufficientDataError(
                "I-MR chart requires at least 2 individual observations to compute a moving range."
            )

        values = [sg.values[0] for sg in individuals]
        moving_ranges = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]

        xbar = statistics.fmean(values)
        mrbar = statistics.fmean(moving_ranges)
        sigma_within = mrbar / D2_MOVING_RANGE_2

        individuals_center_line = xbar
        individuals_ucl = xbar + 3 * sigma_within
        individuals_lcl = xbar - 3 * sigma_within

        mr_center_line = mrbar
        mr_ucl = D4_MOVING_RANGE_2 * mrbar
        mr_lcl = max(D3_MOVING_RANGE_2 * mrbar, 0.0)

        individuals_points = [
            ChartPoint(index=i, subgroup_id=sg.subgroup_id, timestamp=sg.end_timestamp, value=sg.values[0], n=1)
            for i, sg in enumerate(individuals)
        ]
        # Moving range series has one fewer point than individuals (first
        # individual has no predecessor to range against).
        mr_points = [
            ChartPoint(
                index=i + 1,
                subgroup_id=individuals[i + 1].subgroup_id,
                timestamp=individuals[i + 1].end_timestamp,
                value=mr,
                n=2,
            )
            for i, mr in enumerate(moving_ranges)
        ]

        result = ChartResult(
            chart_type=ChartType.IMR,
            primary_chart=ChartSeries(
                center_line=individuals_center_line, ucl=individuals_ucl, lcl=individuals_lcl, points=individuals_points
            ),
            secondary_chart=ChartSeries(center_line=mr_center_line, ucl=mr_ucl, lcl=mr_lcl, points=mr_points),
            grand_mean=xbar,
            subgroup_size_used=1,
        )
        return result, []

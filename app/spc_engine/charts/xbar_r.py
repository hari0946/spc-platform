"""XBAR-R chart: subgroup means (Xbar) with range-based control limits,
paired with the R (range) chart. Standard choice for rational subgroups of
size 2..8.
"""

from __future__ import annotations

import statistics

from app.spc_engine.charts.base_chart import BaseChart, grand_mean_of_means, select_conforming_subgroups
from app.spc_engine.core.constants import get_constants
from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.models import ChartPoint, ChartResult, ChartSeries, Subgroup


class XbarRChart(BaseChart):
    def calculate(self, subgroups: list[Subgroup]) -> tuple[ChartResult, list[str]]:
        conforming, n, warnings = select_conforming_subgroups(subgroups)
        constants = get_constants(n)

        xbarbar = grand_mean_of_means(conforming)
        rbar = statistics.fmean(sg.range_ for sg in conforming)

        xbar_center_line = xbarbar
        xbar_ucl = xbarbar + constants.A2 * rbar
        xbar_lcl = xbarbar - constants.A2 * rbar

        r_center_line = rbar
        r_ucl = constants.D4 * rbar
        r_lcl = constants.D3 * rbar

        xbar_points = [
            ChartPoint(index=i, subgroup_id=sg.subgroup_id, timestamp=sg.end_timestamp, value=sg.mean, n=sg.count)
            for i, sg in enumerate(conforming)
        ]
        r_points = [
            ChartPoint(index=i, subgroup_id=sg.subgroup_id, timestamp=sg.end_timestamp, value=sg.range_, n=sg.count)
            for i, sg in enumerate(conforming)
        ]

        result = ChartResult(
            chart_type=ChartType.XBAR_R,
            primary_chart=ChartSeries(center_line=xbar_center_line, ucl=xbar_ucl, lcl=xbar_lcl, points=xbar_points),
            secondary_chart=ChartSeries(center_line=r_center_line, ucl=r_ucl, lcl=max(r_lcl, 0.0), points=r_points),
            grand_mean=xbarbar,
            subgroup_size_used=n,
        )
        return result, warnings

"""XBAR-S chart: subgroup means (Xbar) with standard-deviation-based control
limits, paired with the S (standard deviation) chart. Preferred over
XBAR-R for larger rational subgroups (n >= 9) since it is statistically
more efficient than the range for larger n.
"""

from __future__ import annotations

import statistics

from app.spc_engine.charts.base_chart import BaseChart, grand_mean_of_means, select_conforming_subgroups
from app.spc_engine.core.constants import get_constants
from app.spc_engine.core.enums import ChartType
from app.spc_engine.core.exceptions import InvalidSubgroupSizeError
from app.spc_engine.core.models import ChartPoint, ChartResult, ChartSeries, Subgroup


class XbarSChart(BaseChart):
    def calculate(self, subgroups: list[Subgroup]) -> tuple[ChartResult, list[str]]:
        conforming, n, warnings = select_conforming_subgroups(subgroups)
        if n < 2:
            raise InvalidSubgroupSizeError("XBAR-S requires subgroup size >= 2 (need a standard deviation).")
        constants = get_constants(n)

        std_devs = [sg.std_dev for sg in conforming if sg.std_dev is not None]
        if len(std_devs) != len(conforming):
            raise InvalidSubgroupSizeError("One or more subgroups is missing a standard deviation.")

        xbarbar = grand_mean_of_means(conforming)
        sbar = statistics.fmean(std_devs)

        xbar_center_line = xbarbar
        xbar_ucl = xbarbar + constants.A3 * sbar
        xbar_lcl = xbarbar - constants.A3 * sbar

        s_center_line = sbar
        s_ucl = constants.B4 * sbar
        s_lcl = constants.B3 * sbar

        xbar_points = [
            ChartPoint(index=i, subgroup_id=sg.subgroup_id, timestamp=sg.end_timestamp, value=sg.mean, n=sg.count)
            for i, sg in enumerate(conforming)
        ]
        s_points = [
            ChartPoint(
                index=i,
                subgroup_id=sg.subgroup_id,
                timestamp=sg.end_timestamp,
                value=sg.std_dev,
                n=sg.count,
            )
            for i, sg in enumerate(conforming)
        ]

        result = ChartResult(
            chart_type=ChartType.XBAR_S,
            primary_chart=ChartSeries(center_line=xbar_center_line, ucl=xbar_ucl, lcl=xbar_lcl, points=xbar_points),
            secondary_chart=ChartSeries(center_line=s_center_line, ucl=s_ucl, lcl=max(s_lcl, 0.0), points=s_points),
            grand_mean=xbarbar,
            subgroup_size_used=n,
        )
        return result, warnings

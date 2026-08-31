"""Ad-hoc smoke test for the SPC engine, run directly with python (not
pytest) during development. Generates a synthetic in-control dataset,
runs a full historical analysis, and prints the result. The formal test
suite lives in tests/spc_engine/.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.spc_engine.core.enums import SubgroupMethod
from app.spc_engine.core.models import RuleConfig, SPCConfiguration, Specification
from app.spc_engine.core.enums import RuleName
from app.spc_engine.results.result_builder import run_spc_analysis


def build_dataset(n: int = 200, mean: float = 20.0, sigma: float = 0.01, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        rows.append(
            {
                "value": random.gauss(mean, sigma),
                "event_timestamp": start + timedelta(minutes=5 * i),
                "machine_id": "CNC_01",
                "product_id": "PART_A",
                "process_id": "MACHINING",
                "operation_id": "OP_10",
                "parameter_id": "SHAFT_DIAMETER",
                "batch_id": None,
                "subgroup_id": None,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    df = build_dataset()
    config = SPCConfiguration(
        chart_type="AUTO",
        subgroup_size=5,
        subgroup_method=SubgroupMethod.CONSECUTIVE,
        maximum_time_gap_seconds=3600,
        minimum_sample_size=20,
        ruleset=[
            RuleConfig(rule_name=RuleName.POINT_OUTSIDE_LIMITS),
            RuleConfig(rule_name=RuleName.TREND_INCREASING, parameters={"consecutive_points": 7}),
            RuleConfig(rule_name=RuleName.TREND_DECREASING, parameters={"consecutive_points": 7}),
            RuleConfig(rule_name=RuleName.RUN_SAME_SIDE, parameters={"consecutive_points": 8}),
        ],
    )
    spec = Specification(lsl=19.94, usl=20.06, target=20.0)

    result = run_spc_analysis(df, config, spec)

    print("Chart type:", result.chart.chart_type)
    print("Selection reason:", result.chart_selection.selection_reason)
    print("Subgroup size used:", result.chart.subgroup_size_used)
    print("Grand mean:", round(result.chart.grand_mean, 5))
    print("Xbar CL/UCL/LCL:", round(result.chart.primary_chart.center_line, 5), round(result.chart.primary_chart.ucl, 5), round(result.chart.primary_chart.lcl, 5))
    print("Within sigma:", round(result.sigma.within_sigma, 6))
    print("Overall sigma:", round(result.sigma.overall_sigma, 6))
    print("Cp/Cpk:", result.capability.cp, result.capability.cpk)
    print("Pp/Ppk:", result.capability.pp, result.capability.ppk)
    print("Stability:", result.stability.status, "violations:", len(result.stability.violations))
    print("Warnings:", result.warnings)


if __name__ == "__main__":
    main()

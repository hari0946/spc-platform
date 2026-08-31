"""Reads an uploaded CSV file into a raw pandas DataFrame.

This module's only job is "bytes on disk -> DataFrame of strings" -- it
performs no validation, mapping, or type coercion. Every value is read as
a string (dtype=str) so downstream validation (validation_pipeline.py) can
make explicit, auditable decisions about type coercion rather than having
pandas silently guess types (e.g. pandas' automatic type inference can
silently turn a mixed numeric/text column into NaN in ways that are hard
to trace back to a specific bad row).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.exceptions import FileValidationError


def read_csv(file_path: str | Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path, dtype=str, keep_default_na=False, na_values=["", "NA", "N/A", "null", "NULL"])
    except pd.errors.EmptyDataError as exc:
        raise FileValidationError("The uploaded CSV file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise FileValidationError(f"The uploaded CSV file could not be parsed: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise FileValidationError(
            "The uploaded CSV file is not valid UTF-8 text. Please re-export it as UTF-8 CSV."
        ) from exc

    if df.empty:
        raise FileValidationError("The uploaded CSV file contains a header but no data rows.")

    # Normalize header whitespace only -- never rename/guess columns here;
    # that is column_mapper.py's explicit, configuration-driven job.
    df.columns = [str(c).strip() for c in df.columns]
    return df

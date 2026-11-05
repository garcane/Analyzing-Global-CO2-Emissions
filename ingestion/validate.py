"""Pre-load validation. Fails before anything is sent to Snowflake."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from ingestion.sources import SourceSpec


class ValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    rows: int
    year_min: int | None
    year_max: int | None


def validate_csv(path: Path, spec: SourceSpec) -> ValidationResult:
    """Check header equals the expected header, file is non-empty, keys are non-null, years plausible."""
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            raise ValidationError(f"{path.name}: file is empty") from None

        if header != spec.columns:
            missing = [c for c in spec.columns if c not in header]
            unexpected = [c for c in header if c not in spec.columns]
            detail = f"missing={missing} unexpected={unexpected}"
            if not missing and not unexpected:
                detail = "same columns but different order"
            raise ValidationError(
                f"{path.name}: header differs from the expected schema ({detail}). "
                "Update ingestion/schemas.py deliberately if the provider changed the format."
            )

        index = {c: i for i, c in enumerate(header)}
        key_idx = [index[c] for c in spec.key_columns]
        year_idx = index[spec.year_column] if spec.year_column else None

        rows = 0
        ymin = ymax = None
        for line_no, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValidationError(f"{path.name} line {line_no}: {len(row)} fields, expected {len(header)}")
            for i in key_idx:
                if row[i] == "":
                    raise ValidationError(f"{path.name} line {line_no}: empty key column '{header[i]}'")
            if year_idx is not None:
                try:
                    year = int(row[year_idx])
                except ValueError:
                    raise ValidationError(
                        f"{path.name} line {line_no}: non-integer year {row[year_idx]!r}"
                    ) from None
                if not (spec.year_min <= year <= spec.year_max):
                    raise ValidationError(
                        f"{path.name} line {line_no}: year {year} outside [{spec.year_min}, {spec.year_max}]"
                    )
                ymin = year if ymin is None else min(ymin, year)
                ymax = year if ymax is None else max(ymax, year)
            rows += 1

    if rows == 0:
        raise ValidationError(f"{path.name}: header present but no data rows")
    return ValidationResult(rows=rows, year_min=ymin, year_max=ymax)

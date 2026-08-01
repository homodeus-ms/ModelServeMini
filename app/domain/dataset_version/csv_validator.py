import csv
from pathlib import Path
from typing import Any


def _is_integer(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _is_boolean(value: str) -> bool:
    return value.strip().lower() in {"true", "false"}


def _infer_value_type(value: str) -> str:
    value = value.strip()

    if value == "":
        return "NULL"

    if _is_integer(value):
        return "INTEGER"

    if _is_float(value):
        return "FLOAT"

    if _is_boolean(value):
        return "BOOLEAN"

    return "STRING"


def _merge_types(current_type: str | None, new_type: str) -> str:
    if current_type is None or current_type == "NULL":
        return new_type

    if new_type == "NULL":
        return current_type

    if current_type == new_type:
        return current_type

    if {current_type, new_type} == {"INTEGER", "FLOAT"}:
        return "FLOAT"

    return "STRING"

# 현재 방식 : 1행이라도 잘못된 데이터가 있으면 VALID : FALSE
# 이후에 확장하는 것으로
def validate_csv(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    row_count = 0
    column_count = 0
    column_names: list[str] = []
    inferred_types: list[str | None] = []
    nullable_columns: list[bool] = []

    try:
        # csv 읽을때는 newline=""
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)

            try:
                header = next(reader)
            except StopIteration:
                return {
                    "valid": False,
                    "row_count": 0,
                    "column_count": 0,
                    "schema_definition": None,
                    "validation_report": {
                        "valid": False,
                        "errors": ["CSV file is empty"],
                        "warnings": []
                    }
                }

            column_names = [name.strip() for name in header]
            column_count = len(column_names)

            if column_count == 0:
                errors.append("CSV header is empty")

            if any(name == "" for name in column_names):
                errors.append("CSV contains an empty column name")

            duplicate_names = {
                name for name in column_names
                if column_names.count(name) > 1
            }

            if duplicate_names:
                errors.append(
                    f"CSV contains duplicate column names: {sorted(duplicate_names)}"
                )

            inferred_types = [None] * column_count
            nullable_columns = [False] * column_count

            for line_number, row in enumerate(reader, start=2):
                if len(row) != column_count:
                    errors.append(
                        f"Line {line_number} has {len(row)} columns; expected {column_count}"
                    )
                    continue

                row_count += 1

                for index, value in enumerate(row):
                    value_type = _infer_value_type(value)

                    if value_type == "NULL":
                        nullable_columns[index] = True

                    inferred_types[index] = _merge_types(
                        inferred_types[index],
                        value_type
                    )

    except UnicodeDecodeError:
        errors.append("CSV file must use UTF-8 encoding")

    except csv.Error as exc:
        errors.append(f"CSV parsing failed: {exc}")

    if row_count == 0 and not errors:
        warnings.append("CSV contains a header but no data rows")

    columns = [
        {
            "name": column_names[index],
            "type": inferred_types[index] or "STRING",
            "nullable": nullable_columns[index]
        }
        for index in range(column_count)
    ]

    valid = len(errors) == 0

    return {
        "valid": valid,
        "row_count": row_count,
        "column_count": column_count,
        "schema_definition": {
            "columns": columns
        },
        "validation_report": {
            "valid": valid,
            "errors": errors,
            "warnings": warnings
        }
    }
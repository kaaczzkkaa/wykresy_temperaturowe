import csv
from datetime import datetime
from pathlib import Path

from essemtec.models import MeasurementSeries, SENSOR_NAMES, SensorName, TemperatureValue


SENSOR_COLUMN_INDEX: dict[SensorName, int] = {
    "T1": 2,
    "T2": 4,
    "T3": 6,
    "T4": 8,
}


def load_temperature_csv(file_path: str | Path) -> MeasurementSeries:
    path = Path(file_path)
    time_axis: list[float] = []
    points: dict[SensorName, list[TemperatureValue]] = {sensor: [] for sensor in SENSOR_NAMES}
    first_timestamp: datetime | None = None

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        row = parse_csv_row(line)
        if not is_measurement_row(row):
            continue

        try:
            current_time = parse_timestamp(row[0], row[1])
        except ValueError:
            continue

        if first_timestamp is None:
            first_timestamp = current_time

        time_axis.append((current_time - first_timestamp).total_seconds())
        for sensor, column_index in SENSOR_COLUMN_INDEX.items():
            value = clean_temperature(row[column_index]) if len(row) > column_index else None
            points[sensor].append(value)

    return MeasurementSeries(source_path=path, time_axis=time_axis, points=points)


def parse_csv_row(line: str) -> list[str]:
    stripped_line = line.strip()
    if not stripped_line:
        return []

    delimiter = ";" if ";" in stripped_line else ","
    return [cell.strip() for cell in next(csv.reader([stripped_line], delimiter=delimiter))]


def is_measurement_row(row: list[str]) -> bool:
    return len(row) >= 3 and row[0].strip().startswith("202")


def parse_timestamp(date_value: str, time_value: str) -> datetime:
    normalized = f"{date_value.strip()} {time_value.strip()}".replace("-", "/")
    for date_format in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(normalized, date_format)
        except ValueError:
            pass
    raise ValueError(f"Unsupported timestamp format: {normalized}")


def clean_temperature(raw_value: str) -> float | None:
    value = raw_value.strip().replace("(", "").replace(")", "")
    normalized = value.replace(" ", "")
    if not normalized or normalized in {"-", "--"} or "null" in normalized.lower():
        return None

    try:
        return float(normalized)
    except ValueError:
        return None

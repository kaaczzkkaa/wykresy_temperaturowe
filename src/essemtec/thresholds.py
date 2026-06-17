from collections.abc import Iterable, Sequence

from essemtec.models import SensorName, TemperatureValue, ThresholdZone


def parse_threshold_values(values: Iterable[str]) -> list[float]:
    thresholds: list[float] = []
    for value in values:
        text = value.strip()
        if not text:
            continue
        try:
            thresholds.append(float(text))
        except ValueError:
            continue
    return sorted(set(thresholds))


def calculate_threshold_zones(
    time_axis: Sequence[float],
    reference_points: Sequence[TemperatureValue],
    thresholds: Iterable[float],
    sensor: SensorName,
) -> list[ThresholdZone]:
    ordered_thresholds = sorted(set(thresholds))
    time_and_temperature = list(zip(time_axis, reference_points))
    raw_zones: dict[float, list[float]] = {}

    for threshold in ordered_thresholds:
        start = first_crossing_time(time_and_temperature, threshold)
        end = last_crossing_time(time_and_temperature, threshold)

        if start is not None and end is not None and end > start:
            raw_zones[threshold] = [start, end]

    trim_lower_zones(raw_zones)

    zones: list[ThresholdZone] = []
    for threshold in ordered_thresholds:
        if threshold not in raw_zones:
            continue

        start, end = raw_zones[threshold]
        if end > start:
            zones.append(ThresholdZone(threshold=threshold, sensor=sensor, start=start, end=end))

    return zones


def first_crossing_time(time_and_temperature: Sequence[tuple[float, TemperatureValue]], threshold: float) -> float | None:
    for time_value, temperature in time_and_temperature:
        if temperature is not None and temperature >= threshold:
            return time_value
    return None


def last_crossing_time(time_and_temperature: Sequence[tuple[float, TemperatureValue]], threshold: float) -> float | None:
    for time_value, temperature in reversed(time_and_temperature):
        if temperature is not None and temperature >= threshold:
            return time_value
    return None


def trim_lower_zones(raw_zones: dict[float, list[float]]) -> None:
    thresholds_from_highest = sorted(raw_zones.keys(), reverse=True)
    for index, higher_threshold in enumerate(thresholds_from_highest):
        higher_start, _higher_end = raw_zones[higher_threshold]
        for lower_threshold in thresholds_from_highest[index + 1 :]:
            lower_start, lower_end = raw_zones[lower_threshold]
            if lower_start < higher_start < lower_end:
                raw_zones[lower_threshold][1] = higher_start

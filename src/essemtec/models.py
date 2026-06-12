from dataclasses import dataclass
from pathlib import Path
from typing import Literal


SensorName = Literal["T1", "T2", "T3", "T4"]
SENSOR_NAMES: tuple[SensorName, ...] = ("T1", "T2", "T3", "T4")
TemperatureValue = float | None


@dataclass(frozen=True)
class MeasurementSeries:
    source_path: Path
    time_axis: list[float]
    points: dict[SensorName, list[TemperatureValue]]

    @property
    def has_rows(self) -> bool:
        return bool(self.time_axis)

    def has_sensor_data(self, sensor: SensorName) -> bool:
        return any(value is not None for value in self.points[sensor])


@dataclass(frozen=True)
class ThresholdZone:
    threshold: float
    sensor: SensorName
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start

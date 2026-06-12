from pathlib import Path
from typing import cast
import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons, TextBox as MatplotlibTextBox

from essemtec.data_loader import load_temperature_csv
from essemtec.models import MeasurementSeries, SENSOR_NAMES, SensorName
from essemtec.thresholds import calculate_threshold_zones, parse_threshold_values


CSV_FILE_TYPES = [("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
SENSOR_STYLES = {
    "T1": {"color": "darkred", "linewidth": 2},
    "T2": {"color": "darkblue", "linewidth": 1.5},
    "T3": {"color": "darkgreen", "linewidth": 2},
    "T4": {"color": "orange", "linewidth": 1.5},
}
ZONE_COLORS = ["purple", "crimson", "teal"]


class ResizeSafeTextBox(MatplotlibTextBox):
    def _resize(self, event: object) -> None:
        # Matplotlib 3.11 decorates TextBox._resize as if ResizeEvent had inaxes.
        self.stop_typing()


def ask_for_csv_file(title: str) -> Path | None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected_file = filedialog.askopenfilename(title=title, filetypes=CSV_FILE_TYPES)
    finally:
        root.destroy()

    if not selected_file:
        return None
    return Path(selected_file)


class TemperaturePlotApp:
    def __init__(self, measurement: MeasurementSeries) -> None:
        self.measurement = measurement
        self.selected_sensor: SensorName = "T1"
        self.dynamic_elements: list[object] = []

        self.figure = plt.figure(figsize=(15, 8))
        self.axis = plt.axes([0.06, 0.1, 0.74, 0.8])
        self.threshold_boxes: list[ResizeSafeTextBox] = []

        self._draw_base_plot()
        self._build_controls()

    def run(self) -> None:
        plt.show()

    def _draw_base_plot(self) -> None:
        self.axis.clear()
        self.axis.grid(True, linestyle="--", alpha=0.5)
        self.axis.set_title("PROFIL TEMPERATUROWY", fontsize=12, fontweight="bold")
        self.axis.set_xlabel("Czas (Sekundy)", fontsize=10)
        self.axis.set_ylabel("Temperatura (C)", fontsize=10)

        for sensor in SENSOR_NAMES:
            if self.measurement.has_sensor_data(sensor):
                self.axis.plot(
                    self.measurement.time_axis,
                    self.measurement.points[sensor],
                    label=sensor,
                    **SENSOR_STYLES[sensor],
                )

        self.axis.legend(loc="upper left")
        self.axis.relim()
        self.axis.autoscale_view()

    def _build_controls(self) -> None:
        box_axes = [
            plt.axes([0.86, 0.80, 0.08, 0.04]),
            plt.axes([0.86, 0.70, 0.08, 0.04]),
            plt.axes([0.86, 0.60, 0.08, 0.04]),
        ]

        for y_pos, label in [(0.85, "Prog Temp 1 (C):"), (0.75, "Prog Temp 2 (C):"), (0.65, "Prog Temp 3 (C):")]:
            self.figure.text(0.86, y_pos, label, fontweight="bold", fontsize=9)

        self.threshold_boxes = [ResizeSafeTextBox(axis, "") for axis in box_axes]

        self.figure.text(0.86, 0.53, "Mierz zakres dla:", fontweight="bold", fontsize=9)
        sensor_axis = plt.axes([0.86, 0.36, 0.08, 0.15], facecolor="lightgray")
        self.sensor_radio = RadioButtons(sensor_axis, SENSOR_NAMES, active=0)

        button_axis = plt.axes([0.86, 0.20, 0.10, 0.05])
        self.file_button = Button(button_axis, "Wybierz inny plik", color="lightblue", hovercolor="skyblue")

        for box in self.threshold_boxes:
            box.on_submit(self.recalculate_ranges)

        self.sensor_radio.on_clicked(self.change_sensor)
        self.file_button.on_clicked(self.load_new_file)

    def _clear_dynamic_elements(self) -> None:
        for element in self.dynamic_elements:
            try:
                element.remove()
            except Exception:
                pass
        self.dynamic_elements.clear()

    def recalculate_ranges(self, _submitted_text: str | None = None) -> None:
        self._clear_dynamic_elements()

        thresholds = parse_threshold_values(box.text for box in self.threshold_boxes)
        if not thresholds:
            self.figure.canvas.draw_idle()
            return

        if not self.measurement.has_sensor_data(self.selected_sensor):
            print(f"Ostrzezenie: Brak danych pomiarowych dla czujnika {self.selected_sensor}!")
            self.figure.canvas.draw_idle()
            return

        zones = calculate_threshold_zones(
            self.measurement.time_axis,
            self.measurement.points[self.selected_sensor],
            thresholds,
            self.selected_sensor,
        )

        for index, zone in enumerate(zones):
            color = ZONE_COLORS[index % len(ZONE_COLORS)]
            line_start = self.axis.axvline(x=zone.start, color=color, linestyle="--", alpha=0.7, linewidth=1.2)
            line_end = self.axis.axvline(x=zone.end, color=color, linestyle="--", alpha=0.7, linewidth=1.2)
            span = self.axis.axvspan(zone.start, zone.end, color=color, alpha=0.08)
            self.dynamic_elements.extend([line_start, line_end, span])

            y_min, y_max = self.axis.get_ylim()
            y_position = y_min + (y_max - y_min) * (0.04 + (index * 0.08))
            center = zone.start + (zone.end - zone.start) / 2

            label = self.axis.text(
                center,
                y_position,
                (
                    f"Prog: {zone.threshold:g}C ({zone.sensor})\n"
                    f"{zone.start:.1f}s - {zone.end:.1f}s\n"
                    f"Czas: {zone.duration:.1f}s"
                ),
                color=color,
                fontweight="bold",
                fontsize=8,
                ha="center",
                bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none"},
            )
            self.dynamic_elements.append(label)

        self.figure.canvas.draw_idle()

    def change_sensor(self, label: str) -> None:
        if label not in SENSOR_NAMES:
            return
        self.selected_sensor = cast(SensorName, label)
        print(f"Zmieniono czujnik pomiarowy na: {self.selected_sensor}")
        self.recalculate_ranges()

    def load_new_file(self, _event: object) -> None:
        print("Otwieranie eksploratora dla nowego pliku...")
        selected_file = ask_for_csv_file("Wybierz nowy plik z pomiaru UT325F (CSV)")
        if selected_file is None:
            return

        try:
            measurement = load_temperature_csv(selected_file)
        except Exception as exc:
            print(f"Blad podczas odczytu pliku: {exc}")
            return

        if not measurement.has_rows:
            print("Brak prawidlowych danych w wybranym pliku.")
            return

        self.measurement = measurement
        self._clear_dynamic_elements()
        self._draw_base_plot()
        self.recalculate_ranges()
        print("Pomyslnie zaladowano nowy wykres!")


def run_app(initial_csv_file: str | Path | None = None) -> int:
    if initial_csv_file is None:
        print("Oczekiwanie na wybor pliku przez uzytkownika...")
        csv_file = ask_for_csv_file("Wybierz plik z pomiaru UT325F (CSV)")
    else:
        csv_file = Path(initial_csv_file)

    if csv_file is None:
        print("Anulowano wybor pliku. Zamykanie programu.")
        return 0

    try:
        measurement = load_temperature_csv(csv_file)
    except Exception as exc:
        print(f"Blad podczas odczytu pliku: {exc}")
        return 1

    if not measurement.has_rows:
        print("Brak prawidlowych danych. Zamykanie programu.")
        return 1

    print(f"Odczytano punktow pomiarowych: {len(measurement.time_axis)}")
    print("Rysowanie wykresu...")
    TemperaturePlotApp(measurement).run()
    return 0

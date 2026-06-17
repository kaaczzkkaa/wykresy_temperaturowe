from essemtec.data_loader import clean_temperature, load_temperature_csv


def test_clean_temperature_handles_missing_markers() -> None:
    assert clean_temperature("-") is None
    assert clean_temperature("- -") is None
    assert clean_temperature("null") is None
    assert clean_temperature("(42.5)") == 42.5


def test_load_temperature_csv_reads_ut325f_export(tmp_path) -> None:
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "\n".join(
            [
                "UT325F,",
                "Date,Time,T1(C),thermocouple,T2(C),thermocouple,T3(C),thermocouple,T4(C),thermocouple,",
                "2026/06/09,09:54:28,29.5,K,29.8,K,- -,K,- -,K,",
                "2026/06/09,09:54:29,30.0,K,30.2,K,- -,K,- -,K,",
            ]
        ),
        encoding="utf-8",
    )

    measurement = load_temperature_csv(csv_file)

    assert measurement.time_axis == [0.0, 1.0]
    assert measurement.points["T1"] == [29.5, 30.0]
    assert measurement.points["T2"] == [29.8, 30.2]
    assert measurement.points["T3"] == [None, None]
    assert measurement.has_rows
    assert measurement.has_sensor_data("T1")

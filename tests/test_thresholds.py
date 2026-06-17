from essemtec.thresholds import calculate_threshold_zones, parse_threshold_values


def test_parse_threshold_values_ignores_empty_and_invalid_values() -> None:
    assert parse_threshold_values(["80", "", "abc", "120", "80"]) == [80.0, 120.0]


def test_calculate_threshold_zones_trims_lower_zone_at_higher_threshold() -> None:
    zones = calculate_threshold_zones(
        time_axis=[0, 1, 2, 3, 4, 5],
        reference_points=[20, 40, 60, 70, 50, 30],
        thresholds=[35, 55],
        sensor="T1",
    )

    assert [(zone.threshold, zone.start, zone.end, zone.duration) for zone in zones] == [
        (35, 1, 2, 1),
        (55, 2, 3, 1),
    ]

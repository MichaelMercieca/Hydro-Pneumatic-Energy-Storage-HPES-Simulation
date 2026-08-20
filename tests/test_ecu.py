import pytest

from hpes_sim.ecu import (
    calculate_charging_flow_rate_m3_s,
    calculate_discharging_flow_rate_m3_s,
)


def test_charging_flow_is_positive():
    flow_rate_m3_s = calculate_charging_flow_rate_m3_s(
        electrical_power_w=1_000_000.0,
        pressure_difference_pa=10_000_000.0,
        pump_efficiency=0.8,
    )

    assert flow_rate_m3_s > 0.0


def test_discharging_flow_is_negative():
    flow_rate_m3_s = calculate_discharging_flow_rate_m3_s(
        electrical_power_w=1_000_000.0,
        pressure_difference_pa=10_000_000.0,
        turbine_efficiency=0.9,
    )

    assert flow_rate_m3_s < 0.0


def test_zero_charging_power_gives_zero_flow():
    flow_rate_m3_s = calculate_charging_flow_rate_m3_s(
        electrical_power_w=0.0,
        pressure_difference_pa=10_000_000.0,
        pump_efficiency=0.8,
    )

    assert flow_rate_m3_s == 0.0


def test_zero_discharging_power_gives_zero_flow():
    flow_rate_m3_s = calculate_discharging_flow_rate_m3_s(
        electrical_power_w=0.0,
        pressure_difference_pa=10_000_000.0,
        turbine_efficiency=0.9,
    )

    assert flow_rate_m3_s == 0.0


@pytest.mark.parametrize(
    "pressure_difference_pa",
    [0.0, -1.0],
)
def test_charging_rejects_non_positive_pressure_difference(
    pressure_difference_pa,
):
    with pytest.raises(ValueError):
        calculate_charging_flow_rate_m3_s(
            electrical_power_w=1_000_000.0,
            pressure_difference_pa=pressure_difference_pa,
            pump_efficiency=0.8,
        )


@pytest.mark.parametrize(
    "efficiency",
    [0.0, -0.1, 1.1],
)
def test_charging_rejects_invalid_efficiency(efficiency):
    with pytest.raises(ValueError):
        calculate_charging_flow_rate_m3_s(
            electrical_power_w=1_000_000.0,
            pressure_difference_pa=10_000_000.0,
            pump_efficiency=efficiency,
        )


@pytest.mark.parametrize(
    "pressure_difference_pa",
    [0.0, -1.0],
)
def test_discharging_rejects_non_positive_pressure_difference(
    pressure_difference_pa,
):
    with pytest.raises(ValueError):
        calculate_discharging_flow_rate_m3_s(
            electrical_power_w=1_000_000.0,
            pressure_difference_pa=pressure_difference_pa,
            turbine_efficiency=0.8,
        )


@pytest.mark.parametrize(
    "efficiency",
    [0.0, -0.1, 1.1],
)
def test_discharging_rejects_invalid_efficiency(efficiency):
    with pytest.raises(ValueError):
        calculate_discharging_flow_rate_m3_s(
            electrical_power_w=1_000_000.0,
            pressure_difference_pa=10_000_000.0,
            turbine_efficiency=efficiency,
        )

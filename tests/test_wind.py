import pytest
import xarray as xr

from factories import make_valid_wind_turbine_parameters
from hpes_sim.wind import (
    calculate_turbine_power_w,
    calculate_wind_farm_power_w,
    calculate_wind_speed_m_s,
    repeat_power_samples,
)


def test_wind_speed_is_vector_magnitude():
    dataset = xr.Dataset(
        {
            "u100": ("valid_time", [3.0]),
            "v100": ("valid_time", [4.0]),
        }
    )

    wind_speed_m_s = calculate_wind_speed_m_s(dataset)

    assert wind_speed_m_s.item() == pytest.approx(5.0)


@pytest.mark.parametrize("wind_speed_m_s", [0.0, 2.9, 3.0, 25.0, 30.0])
def test_turbine_produces_zero_outside_operating_range(wind_speed_m_s):
    power_w = calculate_turbine_power_w(
        wind_speed_m_s,
        make_valid_wind_turbine_parameters(),
    )

    assert power_w == 0.0


def test_turbine_power_is_between_zero_and_rated_below_rated_speed():
    parameters = make_valid_wind_turbine_parameters()

    power_w = calculate_turbine_power_w(7.0, parameters)

    assert 0.0 < power_w < parameters.rated_power_w


@pytest.mark.parametrize("wind_speed_m_s", [11.0, 15.0, 24.9])
def test_turbine_produces_rated_power_in_rated_region(wind_speed_m_s):
    parameters = make_valid_wind_turbine_parameters()

    power_w = calculate_turbine_power_w(wind_speed_m_s, parameters)

    assert power_w == parameters.rated_power_w


def test_wind_farm_power_scales_by_number_of_turbines():
    parameters = make_valid_wind_turbine_parameters(number_of_turbines=10)
    wind_speed_m_s = xr.DataArray([11.0], dims="valid_time")

    power_w = calculate_wind_farm_power_w(wind_speed_m_s, parameters)

    assert power_w.item() == pytest.approx(
        10 * parameters.rated_power_w
    )


def test_turbine_power_rejects_negative_wind_speed():
    with pytest.raises(ValueError):
        calculate_turbine_power_w(
            -1.0,
            make_valid_wind_turbine_parameters(),
        )


def test_repeat_power_samples_holds_each_value_over_substeps():
    expanded = repeat_power_samples(
        power_series_w=[10.0, 20.0],
        sample_interval_s=3600.0,
        simulation_time_step_s=1200.0,
    )

    assert expanded == (10.0, 10.0, 10.0, 20.0, 20.0, 20.0)


def test_repeat_power_samples_rejects_noninteger_time_ratio():
    with pytest.raises(ValueError, match="integer multiple"):
        repeat_power_samples(
            power_series_w=[10.0],
            sample_interval_s=3600.0,
            simulation_time_step_s=1000.0,
        )

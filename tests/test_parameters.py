import pytest

# from hpes_sim.parameters import PCSParameters
from factories import (
    make_valid_ecu_parameters,
    make_valid_pcs_parameters,
    make_valid_wind_turbine_parameters,
)


def test_pcs_values():
    params = make_valid_pcs_parameters()
    
    assert params.total_volume_m3 == 4080.0


def test_pcs_parameters_reject_nonpositive_initial_gas_volume():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(initial_gas_volume_m3=0.0)


def test_pcs_parameters_reject_initial_gas_volume_above_total_volume():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(initial_gas_volume_m3=5000.0)


def test_pcs_parameters_reject_nonpositive_minimum_pressure():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(minimum_absolute_pressure_pa=0.0)


def test_pcs_parameters_reject_maximum_pressure_below_minimum():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(
            minimum_absolute_pressure_pa=10e6,
            maximum_absolute_pressure_pa=9e6,
        )


def test_pcs_parameters_reject_initial_pressure_outside_operating_range():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(initial_absolute_pressure_pa=30e6)


def test_pcs_parameters_reject_nonpositive_temperature():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(initial_temperature_k=0.0)


def test_pcs_parameters_reject_nonpositive_specific_gas_constant():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(specific_gas_constant_j_kg_k=0.0)


def test_pcs_parameters_reject_nonpositive_specific_heat_cv():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(specific_heat_cv_j_kg_k=0.0)


def test_pcs_parameters_reject_negative_heat_transfer_coefficient():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(
            heat_transfer_coefficient_w_m2_k=-1.0
        )


def test_pcs_parameters_reject_nonpositive_heat_transfer_area():
    with pytest.raises(ValueError):
        make_valid_pcs_parameters(heat_transfer_area_m2=0.0)


def test_pcs_parameters_accept_initial_volume_equal_to_total():
    params = make_valid_pcs_parameters(initial_gas_volume_m3=4080.0)

    assert params.initial_gas_volume_m3 == params.total_volume_m3


def test_pcs_parameters_allow_initial_absolute_pressure_boundaries():
    params = make_valid_pcs_parameters()

    at_minimum = make_valid_pcs_parameters(
        initial_absolute_pressure_pa=params.minimum_absolute_pressure_pa
    )
    at_maximum = make_valid_pcs_parameters(
        initial_absolute_pressure_pa=params.maximum_absolute_pressure_pa
    )

    assert (at_minimum.initial_absolute_pressure_pa == params.minimum_absolute_pressure_pa)
    assert (at_maximum.initial_absolute_pressure_pa == params.maximum_absolute_pressure_pa)


@pytest.mark.parametrize(
    "pump_efficiency",
    [0.0, -0.1, 1.1],
)
def test_ecu_parameters_reject_invalid_pump_efficiency(pump_efficiency):
    with pytest.raises(ValueError):
        make_valid_ecu_parameters(pump_efficiency=pump_efficiency)


@pytest.mark.parametrize(
    "turbine_efficiency",
    [0.0, -0.1, 1.1],
)
def test_ecu_parameters_reject_invalid_turbine_efficiency(
    turbine_efficiency,
):
    with pytest.raises(ValueError):
        make_valid_ecu_parameters(turbine_efficiency=turbine_efficiency)


@pytest.mark.parametrize("rated_power_w", [0.0, -1.0])
def test_wind_turbine_parameters_reject_nonpositive_rated_power(
    rated_power_w,
):
    with pytest.raises(ValueError):
        make_valid_wind_turbine_parameters(rated_power_w=rated_power_w)


@pytest.mark.parametrize("number_of_turbines", [0, -1])
def test_wind_turbine_parameters_reject_nonpositive_turbine_count(
    number_of_turbines,
):
    with pytest.raises(ValueError):
        make_valid_wind_turbine_parameters(
            number_of_turbines=number_of_turbines
        )


def test_wind_turbine_parameters_reject_misordered_speed_limits():
    with pytest.raises(ValueError):
        make_valid_wind_turbine_parameters(
            cut_in_speed_m_s=12.0,
            rated_speed_m_s=11.0,
        )

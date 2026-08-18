import pytest

from hpes_sim.parameters import (
    EnvironmentParameters, PCSParameters, SimulationSettings
)

def make_valid_pcs_parameters(**overrides):
    """
    Creates valid defaults for `PCSParameters`, overriding selected 
    values via keyword arguments to reduce boilerplate during tests.
    
    Uses a factory design patter for creating objects. 
    """
    values = {
        "total_volume_m3": 4080.0,
        "initial_gas_volume_m3": 3000.0,
        "initial_absolute_pressure_pa": 8.5e6,
        "initial_temperature_k": 287.15,
        "heat_transfer_coefficient_w_m2_k": 10.0,
        "heat_transfer_area_m2": 500.0,
    }
    
    values.update(overrides)    # Updates defaults with overriden values
    
    return PCSParameters(**values)  # Repacks key-value pairs into kwargs for `PCSParameters`


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
    total_volume_default_value = make_valid_pcs_parameters().total_volume_m3
    assert make_valid_pcs_parameters(initial_gas_volume_m3=total_volume_default_value)


def test_pcs_parameters_allow_initial_absolute_pressure_boundaries():
    params = make_valid_pcs_parameters()
    max_pressure_default = params.maximum_absolute_pressure_pa
    min_pressure_default = params.minimum_absolute_pressure_pa
    assert make_valid_pcs_parameters(maximum_absolute_pressure_pa=max_pressure_default, 
                                     minimum_absolute_pressure_pa=min_pressure_default)

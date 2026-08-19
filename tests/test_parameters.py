import pytest

# from hpes_sim.parameters import PCSParameters
from factories import make_valid_pcs_parameters


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

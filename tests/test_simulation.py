import pytest

from factories import (
    make_valid_ecu_parameters,
    make_valid_environment_parameters,
    make_valid_hpes_state,
    make_valid_pcs_parameters,
)
from hpes_sim.pcs import calculate_initial_gas_mass_kg
from hpes_sim.simulation import (
    advance_simulation_step,
    calculate_pressure_difference_pa,
)


def test_pressure_difference_uses_seawater_pressure_at_depth():
    environment = make_valid_environment_parameters()
    gas_pressure_pa = 8.5e6

    expected_seawater_pressure_pa = (
        environment.atmospheric_pressure_pa
        + environment.seawater_density_kg_m3
        * environment.gravitational_acceleration_m_s2
        * environment.deployment_depth_m
    )

    pressure_difference_pa = calculate_pressure_difference_pa(
        gas_pressure_pa=gas_pressure_pa,
        environment=environment,
    )

    assert pressure_difference_pa == pytest.approx(
        gas_pressure_pa - expected_seawater_pressure_pa
    )


def test_pressure_difference_rejects_nonpositive_result():
    environment = make_valid_environment_parameters()
    seawater_pressure_pa = (
        environment.atmospheric_pressure_pa
        + environment.seawater_density_kg_m3
        * environment.gravitational_acceleration_m_s2
        * environment.deployment_depth_m
    )

    with pytest.raises(ValueError):
        calculate_pressure_difference_pa(
            gas_pressure_pa=seawater_pressure_pa,
            environment=environment,
        )


def test_idle_step_advances_only_time_at_thermal_equilibrium():
    parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    next_state = advance_simulation_step(
        state=state,
        renewable_power_w=6.0e6,
        target_power_w=6.0e6,
        gas_mass_kg=calculate_initial_gas_mass_kg(parameters),
        parameters=parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=1.0,
    )

    assert next_state.time_s == pytest.approx(state.time_s + 1.0)
    assert next_state.gas_volume_m3 == pytest.approx(state.gas_volume_m3)
    assert next_state.gas_temperature_k == pytest.approx(
        state.gas_temperature_k
    )


def test_surplus_power_charges_pcs():
    parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    next_state = advance_simulation_step(
        state=state,
        renewable_power_w=6.1e6,
        target_power_w=6.0e6,
        gas_mass_kg=calculate_initial_gas_mass_kg(parameters),
        parameters=parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=1.0,
    )

    assert next_state.time_s == pytest.approx(state.time_s + 1.0)
    assert next_state.gas_volume_m3 < state.gas_volume_m3
    assert next_state.gas_temperature_k > state.gas_temperature_k


def test_power_deficit_discharges_pcs():
    parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    next_state = advance_simulation_step(
        state=state,
        renewable_power_w=5.9e6,
        target_power_w=6.0e6,
        gas_mass_kg=calculate_initial_gas_mass_kg(parameters),
        parameters=parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=1.0,
    )

    assert next_state.time_s == pytest.approx(state.time_s + 1.0)
    assert next_state.gas_volume_m3 > state.gas_volume_m3
    assert next_state.gas_temperature_k < state.gas_temperature_k

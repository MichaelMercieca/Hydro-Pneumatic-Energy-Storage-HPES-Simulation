import pytest
from hpes_sim.pcs import (
    calculate_initial_gas_mass_kg, calculate_gas_pressure_pa,
    calculate_heat_transfer_rate_w, calculate_temperature_rate,
    advance_pcs
)
from factories import (
    make_valid_pcs_parameters, make_valid_simulation_settings,
    make_valid_environment_parameters, make_valid_hpes_state
)


def test_ideal_gas_law_round_trip_invariant():
    parameters = make_valid_pcs_parameters()
    state = make_valid_hpes_state()
    
    
    mass_kg = calculate_initial_gas_mass_kg(
        parameters=parameters
    )
    original_pressure_pa = parameters.initial_absolute_pressure_pa
    
    pressure_pa = calculate_gas_pressure_pa(
        specific_gas_constant_j_kg_k=
        parameters.specific_gas_constant_j_kg_k,
        gas_volume_m3=state.gas_volume_m3,
        gas_temperature_k=state.gas_temperature_k,
        gas_mass_kg=mass_kg
    )
    
    assert pressure_pa == original_pressure_pa


def test_no_heat_flow():
    parameters = make_valid_pcs_parameters()
    environment = make_valid_environment_parameters()
    
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k
    )
    
    heat_transfer_rate_w = calculate_heat_transfer_rate_w(
        environment=environment, 
        gas_temperature_k=state.gas_temperature_k,
        parameters=parameters
    )
    
    assert heat_transfer_rate_w == 0.0


def test_heat_flows_out_when_gas_is_hotter_than_seawater():
    parameters = make_valid_pcs_parameters()
    environment = make_valid_environment_parameters()

    heat_transfer_rate_w = calculate_heat_transfer_rate_w(
        gas_temperature_k=environment.seawater_temperature_k + 10.0,
        environment=environment,
        parameters=parameters,
    )

    assert heat_transfer_rate_w < 0.0


def test_heat_flows_into_gas_when_gas_is_colder_than_seawater():
    parameters = make_valid_pcs_parameters()
    environment = make_valid_environment_parameters()

    heat_transfer_rate_w = calculate_heat_transfer_rate_w(
        gas_temperature_k=environment.seawater_temperature_k - 10.0,
        environment=environment,
        parameters=parameters,
    )

    assert heat_transfer_rate_w > 0.0


def test_calculate_gas_pressure_rejects_zero_volume():
    parameters = make_valid_pcs_parameters()

    with pytest.raises(ValueError):
        calculate_gas_pressure_pa(
            gas_mass_kg=1.0,
            gas_volume_m3=0.0,
            gas_temperature_k=300.0,
            specific_gas_constant_j_kg_k=
                parameters.specific_gas_constant_j_kg_k,
        )


def test_calculate_gas_pressure_rejects_negative_volume():
    parameters = make_valid_pcs_parameters()

    with pytest.raises(ValueError):
        calculate_gas_pressure_pa(
            gas_mass_kg=1.0,
            gas_volume_m3=-1.0,
            gas_temperature_k=300.0,
            specific_gas_constant_j_kg_k=
                parameters.specific_gas_constant_j_kg_k,
        )


def test_equilibrium_with_zero_flow_preserves_pcs_state():
    parameters = make_valid_pcs_parameters()
    environment = make_valid_environment_parameters()

    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    gas_mass_kg = calculate_initial_gas_mass_kg(parameters)

    next_state = advance_pcs(
        state=state,
        hydraulic_flow_rate_m3_s=0.0,
        gas_mass_kg=gas_mass_kg,
        parameters=parameters,
        environment=environment,
        time_step_s=1.0,
    )

    assert next_state.time_s == state.time_s + 1.0
    assert next_state.gas_volume_m3 == state.gas_volume_m3
    assert next_state.gas_temperature_k == state.gas_temperature_k


def test_positive_hydraulic_flow_reduces_gas_volume():
    parameters = make_valid_pcs_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state()

    gas_mass_kg = calculate_initial_gas_mass_kg(parameters)

    flow_rate_m3_s = 0.5
    time_step_s = 2.0

    next_state = advance_pcs(
        state=state,
        hydraulic_flow_rate_m3_s=flow_rate_m3_s,
        gas_mass_kg=gas_mass_kg,
        parameters=parameters,
        environment=environment,
        time_step_s=time_step_s,
    )

    assert next_state.gas_volume_m3 == (
        state.gas_volume_m3 - flow_rate_m3_s * time_step_s
    )


def test_negative_hydraulic_flow_increases_gas_volume():
    parameters = make_valid_pcs_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state()

    gas_mass_kg = calculate_initial_gas_mass_kg(parameters)

    flow_rate_m3_s = -0.5
    time_step_s = 2.0

    next_state = advance_pcs(
        state=state,
        hydraulic_flow_rate_m3_s=flow_rate_m3_s,
        gas_mass_kg=gas_mass_kg,
        parameters=parameters,
        environment=environment,
        time_step_s=time_step_s,
    )

    assert next_state.gas_volume_m3 == (
        state.gas_volume_m3 - flow_rate_m3_s * time_step_s
    )

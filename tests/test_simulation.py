import pytest

from factories import (
    make_valid_ecu_parameters,
    make_valid_environment_parameters,
    make_valid_hpes_state,
    make_valid_pcs_parameters,
)
from hpes_sim.pcs import calculate_initial_gas_mass_kg
from hpes_sim.simulation import (
    SimulationResult,
    advance_simulation_step,
    calculate_pressure_difference_pa,
    run_simulation,
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
    pcs_parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    next_state = advance_simulation_step(
        state=state,
        renewable_power_w=6.0e6,
        target_power_w=6.0e6,
        gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
        pcs_parameters=pcs_parameters,
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
    pcs_parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    next_state = advance_simulation_step(
        state=state,
        renewable_power_w=6.1e6,
        target_power_w=6.0e6,
        gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=1.0,
    )

    assert next_state.time_s == pytest.approx(state.time_s + 1.0)
    assert next_state.gas_volume_m3 < state.gas_volume_m3
    assert next_state.gas_temperature_k > state.gas_temperature_k


def test_power_deficit_discharges_pcs():
    pcs_parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )

    next_state = advance_simulation_step(
        state=state,
        renewable_power_w=5.9e6,
        target_power_w=6.0e6,
        gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=1.0,
    )

    assert next_state.time_s == pytest.approx(state.time_s + 1.0)
    assert next_state.gas_volume_m3 > state.gas_volume_m3
    assert next_state.gas_temperature_k < state.gas_temperature_k


def test_run_simulation_records_initial_and_every_later_state():
    pcs_parameters = make_valid_pcs_parameters()
    ecu_parameters = make_valid_ecu_parameters()
    environment = make_valid_environment_parameters()
    initial_state = make_valid_hpes_state(
        gas_temperature_k=environment.seawater_temperature_k,
    )
    renewable_power_series_w = [6.1e6, 6.0e6, 5.9e6]
    target_power_series_w = [6.0e6, 6.0e6, 6.0e6]

    result = run_simulation(
        initial_state=initial_state,
        renewable_power_series_w=renewable_power_series_w,
        target_power_series_w=target_power_series_w,
        gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=10.0,
    )

    assert isinstance(result, SimulationResult)
    assert result.states[0] is initial_state
    assert len(result.states) == len(renewable_power_series_w) + 1
    assert result.states[-1].time_s == pytest.approx(30.0)


def test_run_simulation_with_no_power_inputs_returns_initial_state_only():
    pcs_parameters = make_valid_pcs_parameters()
    initial_state = make_valid_hpes_state()

    result = run_simulation(
        initial_state=initial_state,
        renewable_power_series_w=[],
        target_power_series_w=[],
        gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
        pcs_parameters=pcs_parameters,
        ecu_parameters=make_valid_ecu_parameters(),
        environment=make_valid_environment_parameters(),
        time_step_s=1.0,
    )

    assert result.states == (initial_state,)


def test_run_simulation_rejects_power_series_of_different_lengths():
    pcs_parameters = make_valid_pcs_parameters()

    with pytest.raises(ValueError, match="equal lengths"):
        run_simulation(
            initial_state=make_valid_hpes_state(),
            renewable_power_series_w=[6.0e6, 7.0e6],
            target_power_series_w=[6.0e6],
            gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
            pcs_parameters=pcs_parameters,
            ecu_parameters=make_valid_ecu_parameters(),
            environment=make_valid_environment_parameters(),
            time_step_s=1.0,
        )


@pytest.mark.parametrize("time_step_s", [0.0, -1.0])
def test_run_simulation_rejects_nonpositive_time_step(time_step_s):
    pcs_parameters = make_valid_pcs_parameters()

    with pytest.raises(ValueError, match="time_step_s"):
        run_simulation(
            initial_state=make_valid_hpes_state(),
            renewable_power_series_w=[],
            target_power_series_w=[],
            gas_mass_kg=calculate_initial_gas_mass_kg(pcs_parameters),
            pcs_parameters=pcs_parameters,
            ecu_parameters=make_valid_ecu_parameters(),
            environment=make_valid_environment_parameters(),
            time_step_s=time_step_s,
        )

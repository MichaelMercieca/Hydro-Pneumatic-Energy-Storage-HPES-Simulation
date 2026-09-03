import pytest

from hpes_sim.controller import (
    calculate_trailing_average_target_power_w,
    determine_control_command, apply_operating_constraints,
    ControlCommand
)
from factories import (
    make_valid_ecu_parameters,
    make_valid_hpes_state,
    make_valid_pcs_parameters,
)
from hpes_sim.state import OperatingMode


def test_surplus_power_requests_charging():
    command = determine_control_command(
        renewable_power_w=8_000_000.0,
        target_power_w=6_000_000.0,
    )

    assert command == ControlCommand(
        mode=OperatingMode.CHARGING,
        electrical_power_w=2_000_000.0,
    )


def test_power_deficit_requests_discharging():
    command = determine_control_command(
        renewable_power_w=4_000_000.0,
        target_power_w=6_000_000.0,
    )

    assert command == ControlCommand(
        mode=OperatingMode.DISCHARGING,
        electrical_power_w=2_000_000.0,
    )


def test_matching_power_requests_idle():
    command = determine_control_command(
        renewable_power_w=6_000_000.0,
        target_power_w=6_000_000.0,
    )

    assert command == ControlCommand(
        mode=OperatingMode.IDLE,
        electrical_power_w=0.0,
    )


def test_charging_capped_by_pump_rating():
    ecu_parameters = make_valid_ecu_parameters()
    pcs_parameters = make_valid_pcs_parameters()
    state = make_valid_hpes_state()
    
    requested_command = determine_control_command(
        renewable_power_w=8_000_000.0,
        target_power_w=1_000_000.0
    )
    
    command = apply_operating_constraints(
        command=requested_command, 
        ecu_parameters=ecu_parameters,
        pcs_parameters=pcs_parameters,
        state=state
    )
    
    assert command == ControlCommand(
        mode=OperatingMode.CHARGING,
        electrical_power_w=pytest.approx(
            ecu_parameters.maximum_charging_power_w
        ),
    )


def test_discharging_capped_by_turbine_rating():
    ecu_parameters = make_valid_ecu_parameters()
    command = apply_operating_constraints(
        command=ControlCommand(OperatingMode.DISCHARGING, 8.0e6),
        state=make_valid_hpes_state(),
        pcs_parameters=make_valid_pcs_parameters(),
        ecu_parameters=ecu_parameters,
    )

    assert command == ControlCommand(
        OperatingMode.DISCHARGING,
        ecu_parameters.maximum_discharging_power_w,
    )


def test_charging_at_minimum_gas_volume_becomes_idle():
    command = apply_operating_constraints(
        command=ControlCommand(OperatingMode.CHARGING, 1.0e6),
        state=make_valid_hpes_state(gas_volume_m3=1200.0),
        pcs_parameters=make_valid_pcs_parameters(),
        ecu_parameters=make_valid_ecu_parameters(),
    )

    assert command == ControlCommand(OperatingMode.IDLE, 0.0)


def test_discharging_at_maximum_gas_volume_becomes_idle():
    command = apply_operating_constraints(
        command=ControlCommand(OperatingMode.DISCHARGING, 1.0e6),
        state=make_valid_hpes_state(gas_volume_m3=3900.0),
        pcs_parameters=make_valid_pcs_parameters(),
        ecu_parameters=make_valid_ecu_parameters(),
    )

    assert command == ControlCommand(OperatingMode.IDLE, 0.0)


def test_idle_command_remains_idle_after_constraints():
    requested_command = ControlCommand(OperatingMode.IDLE, 0.0)

    command = apply_operating_constraints(
        command=requested_command,
        state=make_valid_hpes_state(),
        pcs_parameters=make_valid_pcs_parameters(),
        ecu_parameters=make_valid_ecu_parameters(),
    )

    assert command == requested_command


def test_trailing_average_target_uses_only_present_and_past_power():
    target_power_w = calculate_trailing_average_target_power_w(
        renewable_power_series_w=[10.0, 20.0, 30.0, 40.0],
        window_steps=3,
    )

    assert target_power_w == pytest.approx(
        (10.0, 15.0, 20.0, 30.0)
    )


def test_trailing_average_target_rejects_nonpositive_window():
    with pytest.raises(ValueError):
        calculate_trailing_average_target_power_w(
            renewable_power_series_w=[10.0],
            window_steps=0,
        )

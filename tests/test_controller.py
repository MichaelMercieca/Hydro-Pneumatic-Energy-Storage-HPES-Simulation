from pytest import approx

from hpes_sim.controller import (
    determine_control_command, apply_operating_constraints,
    ControlCommand
)
from factories import (
    make_valid_ecu_parameters, make_valid_environment_parameters,
    make_valid_pcs_parameters, make_valid_hpes_state
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
    environment = make_valid_ecu_parameters()
    pcs_parameters = make_valid_pcs_parameters()
    state = make_valid_hpes_state()
    
    requested_command = determine_control_command(
        renewable_power_w=8_000_000.0,
        target_power_w=1_000_000.0
    )
    
    command = apply_operating_constraints(
        command=requested_command, 
        ecu_parameters=environment,
        gas_pressure_pa=101e5,
        pcs_parameters=pcs_parameters,
        state=state
    )
    
    assert command.electrical_power_w == (
        approx(environment.maximum_charging_power_w)
    )

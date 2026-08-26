"""Control logic for HPES operation."""

from dataclasses import dataclass

from hpes_sim.state import OperatingMode, HPESState
from hpes_sim.parameters import PCSParameters, ECUParameters


@dataclass(frozen=True)
class ControlCommand:
    mode: OperatingMode
    electrical_power_w: float


def determine_control_command(
    renewable_power_w: float,
    target_power_w: float,
) -> ControlCommand:
    """Determine HPES operating mode and requested electrical power."""
    power_difference_w = renewable_power_w - target_power_w

    match power_difference_w:
        case n if n > 0:
            operating_mode = OperatingMode.CHARGING
        case n if n < 0:
            operating_mode = OperatingMode.DISCHARGING
        case _:
            operating_mode = OperatingMode.IDLE

    return ControlCommand(
        mode=operating_mode,
        electrical_power_w=abs(power_difference_w),
    )


def apply_operating_constraints(
    command: ControlCommand,
    state: HPESState,
    gas_pressure_pa: float,
    parameters: PCSParameters,
    ecu_parameters: ECUParameters,
) -> ControlCommand:
    """Limit a requested command to the current operating constraints."""
    if command.mode is OperatingMode.CHARGING:
        if (
            gas_pressure_pa >= parameters.maximum_absolute_pressure_pa
            or state.gas_volume_m3 <= parameters.minimum_gas_volume_m3
        ):
            return ControlCommand(
                mode=OperatingMode.IDLE,
                electrical_power_w=0.0,
            )

        return ControlCommand(
            mode=OperatingMode.CHARGING,
            electrical_power_w=min(
                command.electrical_power_w,
                ecu_parameters.maximum_charging_power_w,
            ),
        )
    if command.mode is OperatingMode.DISCHARGING:
        if (
            gas_pressure_pa <= parameters.minimum_absolute_pressure_pa
            or state.gas_volume_m3 >= parameters.maximum_gas_volume_m3
        ):
            return ControlCommand(
                mode=OperatingMode.IDLE,
                electrical_power_w=0.0,
            )
            
        return ControlCommand(
            mode=OperatingMode.DISCHARGING,
            electrical_power_w=min(
                command.electrical_power_w,
                ecu_parameters.maximum_discharging_power_w
            )
        )
    
    # if idle
    return command
 
"""Control logic for HPES operation."""

from collections.abc import Sequence
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


def calculate_trailing_average_target_power_w(
    renewable_power_series_w: Sequence[float],
    window_steps: int,
) -> tuple[float, ...]:
    """Calculate a causal trailing-average smoothing target."""
    if window_steps <= 0:
        raise ValueError("window_steps must be greater than zero.")

    target_power_series_w = []

    for index in range(len(renewable_power_series_w)):
        window_start = max(0, index - window_steps + 1)
        window = renewable_power_series_w[window_start:index + 1]
        target_power_series_w.append(sum(window) / len(window))

    return tuple(target_power_series_w)


def apply_operating_constraints(
    command: ControlCommand,
    state: HPESState,
    pcs_parameters: PCSParameters,
    ecu_parameters: ECUParameters,
) -> ControlCommand:
    """Apply instantaneous equipment ratings and hard volume stops."""
    if command.mode is OperatingMode.CHARGING:
        if state.gas_volume_m3 <= pcs_parameters.minimum_gas_volume_m3:
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
        if state.gas_volume_m3 >= pcs_parameters.maximum_gas_volume_m3:
            return ControlCommand(
                mode=OperatingMode.IDLE,
                electrical_power_w=0.0,
            )
            
        return ControlCommand(
            mode=OperatingMode.DISCHARGING,
            electrical_power_w=min(
                command.electrical_power_w,
                ecu_parameters.maximum_discharging_power_w
            ),
        )

    return command

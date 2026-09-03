"""Time-marching orchestration for the HPES simulation."""

from collections.abc import Sequence
from dataclasses import dataclass

from hpes_sim.parameters import (
    ECUParameters, EnvironmentParameters, PCSParameters
)
from hpes_sim.state import HPESState, OperatingMode
from hpes_sim.pcs import calculate_gas_pressure_pa, advance_pcs
from hpes_sim.controller import (
    ControlCommand,
    determine_control_command,
    apply_operating_constraints
)
from hpes_sim.ecu import (
    calculate_charging_flow_rate_m3_s,
    calculate_discharging_flow_rate_m3_s
)


@dataclass(frozen=True)
class SimulationResult:
    """Store the complete state history from a simulation run."""

    states: tuple[HPESState, ...]
    steps: tuple["SimulationStepResult", ...] = ()


@dataclass(frozen=True)
class SimulationStepResult:
    """Store state and power accounting for one completed timestep."""

    state: HPESState
    requested_command: ControlCommand
    accepted_command: ControlCommand
    hydraulic_flow_rate_m3_s: float
    grid_power_w: float
    curtailed_power_w: float
    shortfall_power_w: float


def calculate_pressure_difference_pa(
    gas_pressure_pa: float,
    environment: EnvironmentParameters,
) -> float:
    """Calculate hydraulic pressure difference across the ECU."""
    
    seawater_pressure_pa = (
        environment.atmospheric_pressure_pa
        + environment.seawater_density_kg_m3
        * environment.gravitational_acceleration_m_s2
        * environment.deployment_depth_m
    )

    pressure_difference_pa = gas_pressure_pa - seawater_pressure_pa
    
    if pressure_difference_pa <= 0:
        raise ValueError("pressure difference must be greater than zero.")
    
    return pressure_difference_pa


def calculate_hydraulic_flow_rate_m3_s(
    command: ControlCommand,
    pressure_difference_pa: float,
    ecu_parameters: ECUParameters,
) -> float:
    """Convert an accepted electrical command into signed hydraulic flow."""
    match command.mode:
        case OperatingMode.CHARGING:
            return calculate_charging_flow_rate_m3_s(
                electrical_power_w=command.electrical_power_w,
                pressure_difference_pa=pressure_difference_pa,
                pump_efficiency=ecu_parameters.pump_efficiency,
            )
        case OperatingMode.DISCHARGING:
            return calculate_discharging_flow_rate_m3_s(
                electrical_power_w=command.electrical_power_w,
                pressure_difference_pa=pressure_difference_pa,
                turbine_efficiency=ecu_parameters.turbine_efficiency,
            )
        case OperatingMode.IDLE:
            return 0.0


def limit_command_to_next_state(
    command: ControlCommand,
    state: HPESState,
    pressure_difference_pa: float,
    gas_mass_kg: float,
    pcs_parameters: PCSParameters,
    ecu_parameters: ECUParameters,
    environment: EnvironmentParameters,
    time_step_s: float,
) -> ControlCommand:
    """Limit power so the predicted next state stays in its envelope."""
    if command.mode is OperatingMode.IDLE:
        return command

    def predict_next_state(
        electrical_power_w: float,
    ) -> HPESState | None:
        candidate_command = ControlCommand(
            mode=command.mode,
            electrical_power_w=electrical_power_w,
        )
        hydraulic_flow_rate_m3_s = calculate_hydraulic_flow_rate_m3_s(
            command=candidate_command,
            pressure_difference_pa=pressure_difference_pa,
            ecu_parameters=ecu_parameters,
        )

        candidate_gas_volume_m3 = (
            state.gas_volume_m3
            - hydraulic_flow_rate_m3_s * time_step_s
        )
        if not (
            0.0
            < candidate_gas_volume_m3
            <= pcs_parameters.total_volume_m3
        ):
            return None

        return advance_pcs(
            state=state,
            hydraulic_flow_rate_m3_s=hydraulic_flow_rate_m3_s,
            gas_mass_kg=gas_mass_kg,
            pcs_parameters=pcs_parameters,
            environment=environment,
            time_step_s=time_step_s,
        )

    def is_within_operating_envelope(
        candidate_state: HPESState | None,
    ) -> bool:
        if candidate_state is None:
            return False

        candidate_pressure_pa = calculate_gas_pressure_pa(
            gas_mass_kg=gas_mass_kg,
            gas_volume_m3=candidate_state.gas_volume_m3,
            gas_temperature_k=candidate_state.gas_temperature_k,
            specific_gas_constant_j_kg_k=(
                pcs_parameters.specific_gas_constant_j_kg_k
            ),
        )
        return (
            pcs_parameters.minimum_gas_volume_m3
            <= candidate_state.gas_volume_m3
            <= pcs_parameters.maximum_gas_volume_m3
            and pcs_parameters.minimum_absolute_pressure_pa
            <= candidate_pressure_pa
            <= pcs_parameters.maximum_absolute_pressure_pa
        )

    if is_within_operating_envelope(
        predict_next_state(command.electrical_power_w)
    ):
        return command

    if not is_within_operating_envelope(predict_next_state(0.0)):
        return ControlCommand(
            mode=OperatingMode.IDLE,
            electrical_power_w=0.0,
        )

    lower_power_w = 0.0
    upper_power_w = command.electrical_power_w

    for _ in range(50):
        candidate_power_w = (lower_power_w + upper_power_w) / 2.0
        if is_within_operating_envelope(
            predict_next_state(candidate_power_w)
        ):
            lower_power_w = candidate_power_w
        else:
            upper_power_w = candidate_power_w

    if lower_power_w <= 1.0:
        return ControlCommand(
            mode=OperatingMode.IDLE,
            electrical_power_w=0.0,
        )

    return ControlCommand(
        mode=command.mode,
        electrical_power_w=lower_power_w,
    )
    

def advance_simulation_step(
    state: HPESState,
    renewable_power_w: float,
    target_power_w: float,
    gas_mass_kg: float,
    pcs_parameters: PCSParameters,
    ecu_parameters: ECUParameters,
    environment: EnvironmentParameters,
    time_step_s: float,
) -> HPESState:
    """
    Advance the complete HPES model by one timestep.
    
    1. calculate current gas pressure
    2. calculate hydraulic pressure difference
    3. determine controller command
    4. convert command to hydraulic flow through ECU
    5. advance PCS state
    6. return next state
    """
    
    return calculate_simulation_step_result(
        state=state,
        renewable_power_w=renewable_power_w,
        target_power_w=target_power_w,
        gas_mass_kg=gas_mass_kg,
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=time_step_s,
    ).state


def calculate_simulation_step_result(
    state: HPESState,
    renewable_power_w: float,
    target_power_w: float,
    gas_mass_kg: float,
    pcs_parameters: PCSParameters,
    ecu_parameters: ECUParameters,
    environment: EnvironmentParameters,
    time_step_s: float,
) -> SimulationStepResult:
    """Advance one timestep and retain its operating quantities."""
    current_gas_pressure_pa = calculate_gas_pressure_pa(
        gas_mass_kg=gas_mass_kg,
        gas_volume_m3=state.gas_volume_m3,
        gas_temperature_k=state.gas_temperature_k,
        specific_gas_constant_j_kg_k=(
            pcs_parameters.specific_gas_constant_j_kg_k
        ),
    )
    
    pressure_difference_pa = calculate_pressure_difference_pa(
        environment=environment,
        gas_pressure_pa=current_gas_pressure_pa
    )
    
    requested_command = determine_control_command(
        renewable_power_w=renewable_power_w,
        target_power_w=target_power_w,
    )

    control_command = apply_operating_constraints(
        command=requested_command,
        state=state,
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
    )

    control_command = limit_command_to_next_state(
        command=control_command,
        state=state,
        pressure_difference_pa=pressure_difference_pa,
        gas_mass_kg=gas_mass_kg,
        pcs_parameters=pcs_parameters,
        ecu_parameters=ecu_parameters,
        environment=environment,
        time_step_s=time_step_s,
    )

    hydraulic_flow_rate_m3_s = calculate_hydraulic_flow_rate_m3_s(
        command=control_command,
        pressure_difference_pa=pressure_difference_pa,
        ecu_parameters=ecu_parameters,
    )
    
    next_state = advance_pcs(
        state=state, environment=environment, 
        pcs_parameters=pcs_parameters, gas_mass_kg=gas_mass_kg, 
        hydraulic_flow_rate_m3_s=hydraulic_flow_rate_m3_s,
        time_step_s=time_step_s
    )
    
    charging_power_w = (
        control_command.electrical_power_w
        if control_command.mode is OperatingMode.CHARGING
        else 0.0
    )
    discharging_power_w = (
        control_command.electrical_power_w
        if control_command.mode is OperatingMode.DISCHARGING
        else 0.0
    )
    grid_power_w = (
        renewable_power_w - charging_power_w + discharging_power_w
    )

    curtailed_power_w = (
        requested_command.electrical_power_w - charging_power_w
        if requested_command.mode is OperatingMode.CHARGING
        else 0.0
    )
    shortfall_power_w = (
        requested_command.electrical_power_w - discharging_power_w
        if requested_command.mode is OperatingMode.DISCHARGING
        else 0.0
    )

    return SimulationStepResult(
        state=next_state,
        requested_command=requested_command,
        accepted_command=control_command,
        hydraulic_flow_rate_m3_s=hydraulic_flow_rate_m3_s,
        grid_power_w=grid_power_w,
        curtailed_power_w=curtailed_power_w,
        shortfall_power_w=shortfall_power_w,
    )


def run_simulation(
    initial_state: HPESState,
    renewable_power_series_w: Sequence[float],
    target_power_series_w: Sequence[float],
    gas_mass_kg: float,
    pcs_parameters: PCSParameters,
    ecu_parameters: ECUParameters,
    environment: EnvironmentParameters,
    time_step_s: float,
) -> SimulationResult:
    """Run the HPES model over a sequence of power inputs."""
    if len(renewable_power_series_w) != len(target_power_series_w):
        raise ValueError(
            "renewable and target power series must have equal lengths."
        )

    if time_step_s <= 0:
        raise ValueError("time_step_s must be greater than zero.")

    states = [initial_state]
    steps = []
    current_state = initial_state

    for renewable_power_w, target_power_w in zip(
        renewable_power_series_w,
        target_power_series_w,
    ):
        step_result = calculate_simulation_step_result(
            state=current_state,
            renewable_power_w=renewable_power_w,
            target_power_w=target_power_w,
            gas_mass_kg=gas_mass_kg,
            pcs_parameters=pcs_parameters,
            ecu_parameters=ecu_parameters,
            environment=environment,
            time_step_s=time_step_s,
        )
        current_state = step_result.state
        states.append(current_state)
        steps.append(step_result)

    return SimulationResult(
        states=tuple(states),
        steps=tuple(steps),
    )

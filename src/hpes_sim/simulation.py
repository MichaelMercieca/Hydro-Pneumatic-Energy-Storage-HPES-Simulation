"""Time-marching orchestration for the HPES simulation."""

from collections.abc import Sequence
from dataclasses import dataclass

from hpes_sim.parameters import (
    ECUParameters, EnvironmentParameters, PCSParameters
)
from hpes_sim.state import HPESState, OperatingMode
from hpes_sim.pcs import calculate_gas_pressure_pa, advance_pcs
from hpes_sim.controller import determine_control_command
from hpes_sim.ecu import (
    calculate_charging_flow_rate_m3_s,
    calculate_discharging_flow_rate_m3_s
)


@dataclass(frozen=True)
class SimulationResult:
    """Store the complete state history from a simulation run."""

    states: tuple[HPESState, ...]


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
    

def advance_simulation_step(
    state: HPESState,
    renewable_power_w: float,
    target_power_w: float,
    gas_mass_kg: float,
    parameters: PCSParameters,
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
    
    current_gas_pressure_pa = calculate_gas_pressure_pa(
        gas_mass_kg=gas_mass_kg,
        gas_volume_m3=state.gas_volume_m3,
        gas_temperature_k=state.gas_temperature_k,
        specific_gas_constant_j_kg_k=(
            parameters.specific_gas_constant_j_kg_k
        ),
    )
    
    pressure_difference_pa = calculate_pressure_difference_pa(
        environment=environment,
        gas_pressure_pa=current_gas_pressure_pa
    )
    
    control_command = determine_control_command(
        renewable_power_w=renewable_power_w,
        target_power_w=target_power_w
    )
    
    match control_command.mode:
        case OperatingMode.CHARGING:
            hydraulic_flow_rate_m3_s = (
                calculate_charging_flow_rate_m3_s(
                    electrical_power_w=
                    control_command.electrical_power_w,
                    pressure_difference_pa=pressure_difference_pa,
                    pump_efficiency=ecu_parameters.pump_efficiency
                )
            )
            
        case OperatingMode.DISCHARGING:
            hydraulic_flow_rate_m3_s = (
                calculate_discharging_flow_rate_m3_s(
                    electrical_power_w=
                    control_command.electrical_power_w,
                    pressure_difference_pa=pressure_difference_pa,
                    turbine_efficiency=ecu_parameters.turbine_efficiency
                )
            )
        case OperatingMode.IDLE:
            hydraulic_flow_rate_m3_s = 0.0
    
    next_state = advance_pcs(
        state=state, environment=environment, parameters=parameters,
        gas_mass_kg=gas_mass_kg, 
        hydraulic_flow_rate_m3_s=hydraulic_flow_rate_m3_s,
        time_step_s=time_step_s
    )
    
    return next_state


def run_simulation(
    initial_state: HPESState,
    renewable_power_series_w: Sequence[float],
    target_power_series_w: Sequence[float],
    gas_mass_kg: float,
    parameters: PCSParameters,
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
    current_state = initial_state

    for renewable_power_w, target_power_w in zip(
        renewable_power_series_w,
        target_power_series_w,
    ):
        current_state = advance_simulation_step(
            state=current_state,
            renewable_power_w=renewable_power_w,
            target_power_w=target_power_w,
            gas_mass_kg=gas_mass_kg,
            parameters=parameters,
            ecu_parameters=ecu_parameters,
            environment=environment,
            time_step_s=time_step_s,
        )
        states.append(current_state)

    return SimulationResult(states=tuple(states))

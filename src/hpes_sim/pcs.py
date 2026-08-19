"""Thermodynamic model of the HPES pressure containment system."""

from hpes_sim.parameters import EnvironmentParameters, PCSParameters
from hpes_sim.state import HPESState

def calculate_initial_gas_mass_kg(
    parameters: PCSParameters,
) -> float:
    """
    Initialises gas mass using:
    
    m = pV / RT
    """
    return (
        parameters.initial_absolute_pressure_pa
        * parameters.initial_gas_volume_m3
        / (
            parameters.specific_gas_constant_j_kg_k
            * parameters.initial_temperature_k
        )
    )


def calculate_gas_pressure_pa(
    gas_mass_kg: float,
    gas_volume_m3: float,
    gas_temperature_k: float,
    specific_gas_constant_j_kg_k: float,
) -> float:
    """
    Calculates gas pressure using:
    
    p = mRT / V
    """
    if gas_volume_m3 <= 0:
        raise ValueError("gas_volume_m3 must be greater than zero.")
    
    return (
        gas_mass_kg * specific_gas_constant_j_kg_k * gas_temperature_k
        / gas_volume_m3
    )


def calculate_heat_transfer_rate_w(
    gas_temperature_k: float,
    environment: EnvironmentParameters,
    parameters: PCSParameters,
) -> float:
    """
    Calculates heat transfer rate using:
    
    Q(dot) = hA(T_sea - T_gas)
    """        
    return (
        parameters.heat_transfer_coefficient_w_m2_k
        * parameters.heat_transfer_area_m2
        * (
            environment.seawater_temperature_k - gas_temperature_k
        )
    )


def calculate_temperature_rate(
    pressure_pa: float,
    hydraulic_flow_rate_m3_s: float,
    heat_transfer_rate_w: float,
    gas_mass_kg: float,
    specific_heat_cv_j_kg_k: float,
) -> float:
    """
    Calculates temperature rate using:
    
    dT/dt = [Q(dot) + p.Q_h] / m.c_v]
    """
    return (
        (
            heat_transfer_rate_w 
            + pressure_pa * hydraulic_flow_rate_m3_s
        )
        / (gas_mass_kg * specific_heat_cv_j_kg_k)
    )



# TODO: Potential refactor from function `advance_pcs` to an OOP design
#       encompassing parameters and environment [PCSModel(params, env)].
def advance_pcs(
    state: HPESState,
    hydraulic_flow_rate_m3_s: float,
    gas_mass_kg: float,
    parameters: PCSParameters,
    environment: EnvironmentParameters,
    time_step_s: float,
) -> HPESState:
    """
    Calculate next PCS state using:
    
    V_(g,n+1) = V_(g,n) - Q_(h,n).delta_t   [n.b.: dV_g/dt = -Q_h]
    &
    T_(n+1) = T_n + (dT/dt)_n.delta_t
    &
    t_n+1 = t_n + delta_t
    
    Returns:
        HPESState: the next state (n+1)
    """
    heat_transfer_rate_w = calculate_heat_transfer_rate_w(
        parameters=parameters,
        environment=environment,
        gas_temperature_k=state.gas_temperature_k
    )
    gas_pressure_pa = calculate_gas_pressure_pa(
        gas_mass_kg=gas_mass_kg,
        gas_temperature_k=state.gas_temperature_k,
        gas_volume_m3=state.gas_volume_m3,
        specific_gas_constant_j_kg_k=
        parameters.specific_gas_constant_j_kg_k
    )
    temperature_rate = calculate_temperature_rate(
        gas_mass_kg=gas_mass_kg,
        heat_transfer_rate_w=heat_transfer_rate_w,
        hydraulic_flow_rate_m3_s=hydraulic_flow_rate_m3_s,
        pressure_pa=gas_pressure_pa,
        specific_heat_cv_j_kg_k=parameters.specific_gas_constant_j_kg_k
    )
    
    next_gas_volume_m3 = (
        state.gas_volume_m3
        - (
            hydraulic_flow_rate_m3_s
            * time_step_s
        )
    )
    # Later, the controller/ECU should handle the below validation instead.
    if not 0 < next_gas_volume_m3 <= parameters.total_volume_m3:
        raise ValueError("next_gas_volume_m3 must be greater than zero "
                         "and less than or equal to total_volume_m3.")
    
    next_gas_temperature_k = (
        state.gas_temperature_k
        + (temperature_rate * time_step_s)
    )
    
    next_time_s = state.time_s + time_step_s
    
    return HPESState(
        time_s=next_time_s,
        gas_volume_m3=next_gas_volume_m3,
        gas_temperature_k=next_gas_temperature_k
    )

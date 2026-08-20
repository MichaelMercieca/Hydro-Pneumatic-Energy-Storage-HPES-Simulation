"""Energy conversion unit model for the HPES system."""


def calculate_charging_flow_rate_m3_s(
    electrical_power_w: float,
    pressure_difference_pa: float,
    pump_efficiency: float,
) -> float:
    """Calculate PCS hydraulic flow during charging."""
    
    if electrical_power_w < 0:
        raise ValueError("electrical_power_w must be non-negative.")

    if pressure_difference_pa <= 0:
        raise ValueError("pressure_difference_pa must be greater than zero.")

    if not 0 < pump_efficiency <= 1:
        raise ValueError("pump_efficiency must be greater than zero and at most one.")
    
    return(
        (pump_efficiency * electrical_power_w)
        / pressure_difference_pa
    )


def calculate_discharging_flow_rate_m3_s(
    electrical_power_w: float,
    pressure_difference_pa: float,
    turbine_efficiency: float,
) -> float:
    """Calculate PCS hydraulic flow during discharging."""
    
    if electrical_power_w < 0:
        raise ValueError("electrical_power_w must be non-negative.")

    if pressure_difference_pa <= 0:
        raise ValueError("pressure_difference_pa must be greater than zero.")

    if not 0 < turbine_efficiency <= 1:
        raise ValueError("turbine_efficiency must be greater than zero and at most one.")
    
    return(
        # IMP: negative due to sign convention established in `pcs.py`
        -electrical_power_w
        / (turbine_efficiency * pressure_difference_pa)
    )

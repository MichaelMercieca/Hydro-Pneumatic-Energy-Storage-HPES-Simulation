"""Wind-data processing and simplified turbine power conversion."""

from collections.abc import Sequence
from pathlib import Path

import xarray as xr

from hpes_sim.parameters import WindTurbineParameters


def load_era5_wind_dataset(path: Path) -> xr.Dataset:
    """Load an ERA5 NetCDF wind dataset."""
    return xr.open_dataset(path, engine="netcdf4")


def calculate_wind_speed_m_s(
    dataset: xr.Dataset,
) -> xr.DataArray:
    """Calculate 100 m wind-speed magnitude from its vector components."""
    return (
        dataset["u100"] ** 2
        + dataset["v100"] ** 2
    ) ** 0.5


def calculate_turbine_power_w(
    wind_speed_m_s: float,
    parameters: WindTurbineParameters,
) -> float:
    """Calculate one turbine's idealized power using a cubic curve.

    The model assumes perfect yaw alignment and omits air-density variation,
    availability losses, electrical losses, turbulence and wake interactions.
    """
    if wind_speed_m_s < 0:
        raise ValueError("wind_speed_m_s cannot be negative.")

    if wind_speed_m_s < parameters.cut_in_speed_m_s:
        return 0.0

    if wind_speed_m_s < parameters.rated_speed_m_s:
        normalized_cubic_power = (
            wind_speed_m_s**3 - parameters.cut_in_speed_m_s**3
        ) / (
            parameters.rated_speed_m_s**3
            - parameters.cut_in_speed_m_s**3
        )
        return parameters.rated_power_w * normalized_cubic_power

    if wind_speed_m_s < parameters.cut_out_speed_m_s:
        return parameters.rated_power_w

    return 0.0


def calculate_wind_farm_power_w(
    wind_speed_m_s: xr.DataArray,
    parameters: WindTurbineParameters,
) -> xr.DataArray:
    """Apply the simplified turbine curve to a wind-speed time series."""
    # TODO: Replace the idealized curve and direct turbine multiplication with
    # a documented reference-turbine curve and explicit farm-loss model.
    if bool((wind_speed_m_s < 0).any()):
        raise ValueError("wind_speed_m_s cannot contain negative values.")

    normalized_cubic_power = (
        wind_speed_m_s**3 - parameters.cut_in_speed_m_s**3
    ) / (
        parameters.rated_speed_m_s**3
        - parameters.cut_in_speed_m_s**3
    )

    single_turbine_power_w = xr.where(
        wind_speed_m_s < parameters.cut_in_speed_m_s,
        0.0,
        xr.where(
            wind_speed_m_s < parameters.rated_speed_m_s,
            parameters.rated_power_w * normalized_cubic_power,
            xr.where(
                wind_speed_m_s < parameters.cut_out_speed_m_s,
                parameters.rated_power_w,
                0.0,
            ),
        ),
    )

    wind_farm_power_w = (
        single_turbine_power_w * parameters.number_of_turbines
    )
    wind_farm_power_w.name = "wind_farm_power_w"
    wind_farm_power_w.attrs = {
        "long_name": "simplified wind-farm electrical power",
        "units": "W",
    }
    return wind_farm_power_w


def repeat_power_samples(
    power_series_w: Sequence[float],
    sample_interval_s: float,
    simulation_time_step_s: float,
) -> tuple[float, ...]:
    """Hold each measured power sample over smaller solver timesteps."""
    if sample_interval_s <= 0 or simulation_time_step_s <= 0:
        raise ValueError("time intervals must be greater than zero.")

    repetitions = sample_interval_s / simulation_time_step_s
    rounded_repetitions = round(repetitions)

    if not repetitions.is_integer():
        raise ValueError(
            "sample_interval_s must be an integer multiple of "
            "simulation_time_step_s."
        )

    expanded_power_series_w = []
    for power_w in power_series_w:
        expanded_power_series_w.extend(
            [power_w] * rounded_repetitions
        )

    return tuple(expanded_power_series_w)

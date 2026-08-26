"""Wind-data processing for the HPES simulation."""

from pathlib import Path

import xarray as xr


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

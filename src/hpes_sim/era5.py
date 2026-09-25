"""Small, validated ERA5 point requests and safe NetCDF/ZIP decoding."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile

import pandas as pd
import xarray as xr

from hpes_sim.web_model import validate_wind

DATASET = "reanalysis-era5-single-levels-timeseries"
LATITUDE, LONGITUDE = 35.75, 14.75
START_DATE, END_DATE = date(2025, 1, 1), date(2025, 12, 31)


def request_for_dates(start: date, end: date):
    validate_dates(start, end)
    return {"variable": ["100m_u_component_of_wind", "100m_v_component_of_wind"],
            "location": {"longitude": LONGITUDE, "latitude": LATITUDE},
            "date": [f"{start.isoformat()}/{end.isoformat()}"], "data_format": "netcdf"}


def validate_dates(start, end):
    if not START_DATE <= start <= end <= END_DATE:
        raise ValueError("Choose an ordered date range within 2025.")


def select_dates(frame, start, end):
    validate_dates(start, end)
    selected = frame.loc[str(start):str(end)].copy()
    validate_wind(selected)
    expected = pd.date_range(str(start), pd.Timestamp(end) + pd.Timedelta(hours=23), freq="h")
    if not selected.index.equals(expected):
        raise ValueError("ERA5 did not return every requested hour. Choose another date range or retry later.")
    return selected


def read_download(path: Path, start: date, end: date):
    with TemporaryDirectory(prefix="hpes-read-") as directory:
        source = path
        if is_zipfile(path):
            with ZipFile(path) as archive:
                files = [f for f in archive.infolist() if f.filename.endswith(".nc")]
                if len(files) != 1 or files[0].file_size > 20_000_000:
                    raise ValueError("Expected one small NetCDF point time series.")
                source = Path(directory) / "wind.nc"
                source.write_bytes(archive.read(files[0]))
        with xr.open_dataset(source, engine="netcdf4") as dataset:
            time_name = "valid_time" if "valid_time" in dataset.coords else "time"
            for name, expected in (("latitude", LATITUDE), ("longitude", LONGITUDE)):
                if name in dataset.coords and abs(float(dataset[name].values) - expected) > 0.13:
                    raise ValueError("ERA5 returned a different location.")
            arrays = {}
            for name in ("u100", "v100"):
                variable = dataset[name]
                for dim in list(variable.dims):
                    if dim != time_name and variable.sizes[dim] == 1:
                        variable = variable.isel({dim: 0})
                if variable.dims != (time_name,):
                    raise ValueError("Expected a single-point wind time series.")
                arrays[name] = variable.values
            frame = pd.DataFrame(arrays, index=pd.DatetimeIndex(dataset[time_name].values))
    return select_dates(frame.sort_index(), start, end)

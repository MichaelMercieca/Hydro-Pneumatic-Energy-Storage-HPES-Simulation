from pathlib import Path
from zipfile import ZipFile

import cdsapi


DATASET = "reanalysis-era5-single-levels-timeseries"

REQUEST = {
    "variable": [
        "100m_u_component_of_wind",
        "100m_v_component_of_wind",
    ],
    "location": {
        "longitude": 14.75,
        "latitude": 35.75,
    },
    "date": ["2026-01-01/2026-01-07"],
    "data_format": "netcdf",
}


def download_era5_wind(
    archive_path: Path,
    output_path: Path,
) -> None:
    """Download and extract ERA5 wind data."""

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = cdsapi.Client()
    client.retrieve(DATASET, REQUEST, str(archive_path))

    with ZipFile(archive_path) as archive:
        netcdf_files = [
            name
            for name in archive.namelist()
            if name.endswith(".nc")
        ]

        if len(netcdf_files) != 1:
            raise RuntimeError(
                f"Expected exactly one NetCDF file, found: {netcdf_files}"
            )

        with archive.open(netcdf_files[0]) as source:
            output_path.write_bytes(source.read())


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    archive_path = (
        project_root
        / "data"
        / "raw"
        / "era5_wind_2026-01-01_2026-01-07.zip"
    )

    output_path = (
        project_root
        / "data"
        / "processed"
        / "era5_wind.nc"
    )

    download_era5_wind(archive_path, output_path)


if __name__ == "__main__":
    main()

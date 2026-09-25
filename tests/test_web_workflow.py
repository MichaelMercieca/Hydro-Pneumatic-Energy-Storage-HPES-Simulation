from datetime import date
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from hpes_sim.era5 import read_download, request_for_dates, select_dates
from hpes_sim.web_model import Design, simulate, validate_wind

ROOT = Path(__file__).resolve().parents[1]


def wind():
    return pd.read_csv(ROOT / "examples/era5_2025.csv", index_col=0, parse_dates=True).iloc[:48]


@pytest.mark.parametrize("kwargs", [{"volume_m3": 999}, {"depth_m": 201}, {"power_mw": float("nan")},
                                  {"wind_rating_mw": 21}, {"smoothing_hours": 2.5}])
def test_design_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        Design(**kwargs)


def test_date_request_includes_both_dates_and_bounds():
    assert request_for_dates(date(2025, 1, 1), date(2025, 12, 31))["date"] == ["2025-01-01/2025-12-31"]
    for start, end in [(date(2024, 12, 31), date(2025, 1, 1)),
                       (date(2025, 1, 2), date(2025, 1, 1)), (date(2025, 12, 31), date(2026, 1, 1))]:
        with pytest.raises(ValueError):
            request_for_dates(start, end)


@pytest.mark.parametrize("problem", ["missing", "duplicate", "nan"])
def test_bad_wind_is_not_silently_repaired(problem):
    frame = wind()
    if problem == "missing":
        frame = frame.drop(frame.index[3])
    elif problem == "duplicate":
        frame.index = [frame.index[0]] * len(frame)
    else:
        frame.iloc[0, 0] = np.nan
    with pytest.raises(ValueError):
        validate_wind(frame)


def test_incomplete_requested_day_rejected():
    with pytest.raises(ValueError):
        select_dates(wind().iloc[:-1], date(2025, 1, 1), date(2025, 1, 2))


@pytest.mark.parametrize("zipped", [False, True])
def test_netcdf_and_zip_reading(tmp_path, zipped):
    frame = wind()
    path = tmp_path / "input.nc"
    dataset = xr.Dataset({name: ("valid_time", frame[name].values) for name in frame.columns},
                         coords={"valid_time": frame.index, "latitude": 35.75, "longitude": 14.75})
    dataset.to_netcdf(path)
    if zipped:
        archive = tmp_path / "input.zip"
        with ZipFile(archive, "w") as target:
            target.write(path, "nested/wind.nc")
        path = archive
    actual = read_download(path, date(2025, 1, 1), date(2025, 1, 2))
    np.testing.assert_allclose(actual.values, frame.values)


@pytest.mark.parametrize("design", [Design(), Design(1000, 200, 10, 20, 24), Design(6000, 30, 0.5, 1, 2)])
def test_energy_accounting_and_design_extremes(design):
    output, stats = simulate(wind(), design)
    assert len(output) == 48 * 60
    assert np.isfinite(output.values).all()
    np.testing.assert_allclose(output.grid_mw + output.storage_mw, output.wind_mw, atol=1e-12)
    assert (output.residual_error_mw <= output.raw_error_mw + 1e-10).all()
    assert output.storage_mw.abs().max() <= design.power_mw + 1e-10
    assert stats["charged_mwh"] == pytest.approx(output.storage_mw.clip(lower=0).sum() / 60)
    assert stats["discharged_mwh"] == pytest.approx(-output.storage_mw.clip(upper=0).sum() / 60)


def test_zero_wind_does_not_report_spurious_improvement():
    frame = wind() * 0
    output, stats = simulate(frame, Design())
    assert stats["rmse_reduction_percent"] is None
    assert stats["charged_mwh"] == stats["discharged_mwh"] == 0


def test_default_timestep_sensitivity():
    _, coarse = simulate(wind(), Design(), 60)
    _, fine = simulate(wind(), Design(), 30)
    assert coarse["grid_rmse_mw"] == pytest.approx(fine["grid_rmse_mw"], rel=0.03)


def test_processing_batches_match_a_continuous_solver_run(monkeypatch):
    import hpes_sim.web_model as model
    original = model.run_simulation
    calls = []

    def record(*args):
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(model, "run_simulation", record)
    output, _ = model.simulate(wind(), Design())
    first = calls[0]
    continuous = original(first[0], np.concatenate([args[1] for args in calls]),
                          np.concatenate([args[2] for args in calls]), *first[3:])
    np.testing.assert_allclose(output.grid_mw, [step.grid_power_w / 1e6 for step in continuous.steps], rtol=0, atol=0)
    np.testing.assert_allclose(output.gas_volume_m3, [state.gas_volume_m3 for state in continuous.states[1:]], rtol=0, atol=0)


def test_app_runs_and_reconfigures_example():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    assert not app.exception
    next(button for button in app.button if button.label == 'Run simulation').click().run()
    assert not app.exception
    assert len(app.metric) == 3
    first = app.session_state.result[2]["design"]
    app.slider[0].set_value(6000)
    next(button for button in app.button if button.label == 'Run simulation').click().run()
    assert not app.exception
    assert app.session_state.result[2]["design"]["volume_m3"] == 6000
    assert first["volume_m3"] == 4080


def test_app_has_main_page_controls_and_no_data_source_choice():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    assert not app.exception
    assert not app.radio
    assert not app.sidebar.slider
    assert len(app.slider) == 5
    assert app.date_input[0].value == (date(2025, 4, 9), date(2025, 4, 15))
    assert app.date_input[0].min == date(2025, 1, 1)
    assert app.date_input[0].max == date(2025, 12, 31)


def test_bundled_year_is_complete_and_has_matching_provenance():
    import hashlib, json
    path = ROOT / "examples/era5_2025.csv"
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    selected = select_dates(frame, date(2025, 1, 1), date(2025, 12, 31))
    assert len(selected) == 8760
    metadata = json.loads(path.with_suffix(".metadata.json").read_text())
    assert metadata["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_year_boundaries_and_longer_than_month_selection():
    frame = pd.read_csv(ROOT / "examples/era5_2025.csv", index_col=0, parse_dates=True)
    assert len(select_dates(frame, date(2025, 12, 31), date(2025, 12, 31))) == 24
    assert len(select_dates(frame, date(2025, 1, 1), date(2025, 2, 28))) == 59 * 24
    with pytest.raises(ValueError):
        select_dates(frame, date(2024, 12, 31), date(2025, 1, 1))

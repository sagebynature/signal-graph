from __future__ import annotations

import shutil
from types import SimpleNamespace

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_doctor_reports_missing_config_and_toolchain_statuses(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        "signal_graph.cli.doctor.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "config: missing" in result.stdout.lower()
    assert "docker: ok" in result.stdout.lower()
    assert "uv: ok" in result.stdout.lower()
    assert "ty: ok" in result.stdout.lower()


def test_doctor_reports_present_config_even_if_invalid(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".signal-graph"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text("not = [valid")
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        "signal_graph.cli.doctor.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "config: ok" in result.stdout.lower()


def test_doctor_reports_missing_when_config_path_is_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".signal-graph"
    config_dir.mkdir()
    (config_dir / "config.toml").mkdir()
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        "signal_graph.cli.doctor.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "config: missing" in result.stdout.lower()


def test_doctor_fails_when_required_tooling_is_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    def fake_which(name: str) -> str | None:
        if name == "ty":
            return None
        return f"/usr/bin/{name}"

    monkeypatch.setattr(shutil, "which", fake_which)
    monkeypatch.setattr(
        "signal_graph.cli.doctor.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "ty: missing" in result.stdout.lower()

from __future__ import annotations

import shutil
from types import SimpleNamespace

from typer.testing import CliRunner

from signal_graph.cli.main import app


def test_doctor_reports_optional_config_and_runtime_statuses(
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
    assert "config: ok (not present)" in result.stdout.lower()
    assert "neo4j auth: ok" in result.stdout.lower()
    assert "docker: ok" in result.stdout.lower()
    assert "uv: ok" in result.stdout.lower()


def test_doctor_fails_when_config_exists_but_is_invalid(monkeypatch, tmp_path):
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

    assert result.exit_code == 1
    assert "config: error" in result.stdout.lower()
    assert "invalid config toml" in result.stdout.lower()
    assert "neo4j auth: skipped (config invalid)" in result.stdout.lower()


def test_doctor_fails_when_config_path_is_unreadable(monkeypatch, tmp_path):
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

    assert result.exit_code == 1
    assert "config: error" in result.stdout.lower()
    assert "unable to read config" in result.stdout.lower()
    assert "neo4j auth: skipped (config invalid)" in result.stdout.lower()


def test_doctor_fails_when_required_runtime_tooling_is_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    def fake_which(name: str) -> str | None:
        if name == "uv":
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
    assert "uv: missing" in result.stdout.lower()


def test_doctor_allows_missing_ty(monkeypatch, tmp_path):
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

    assert result.exit_code == 0
    assert "docker: ok" in result.stdout.lower()
    assert "uv: ok" in result.stdout.lower()


def test_doctor_fails_when_neo4j_auth_is_malformed(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NEO4J_AUTH", "neo4j")
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        "signal_graph.cli.doctor.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "neo4j auth: error" in result.stdout.lower()
    assert "username/password" in result.stdout.lower()

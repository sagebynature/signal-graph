from __future__ import annotations

import pytest

from signal_graph.config import get_neo4j_config, load_config


def test_load_config_returns_none_when_config_is_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert load_config(tmp_path / ".signal-graph" / "config.toml") is None


def test_load_config_raises_value_error_for_invalid_toml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".signal-graph"
    config_dir.mkdir()
    config_path = config_dir / "config.toml"
    config_path.write_text("not = [valid")

    with pytest.raises(ValueError, match="Invalid config TOML"):
        load_config(config_path)


def test_load_config_raises_value_error_for_unreadable_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".signal-graph"
    config_dir.mkdir()
    config_path = config_dir / "config.toml"
    config_path.mkdir()

    with pytest.raises(ValueError, match="Unable to read config"):
        load_config(config_path)


@pytest.mark.parametrize(
    "auth_value",
    ["neo4j", "neo4j/", "/password", "none"],
)
def test_get_neo4j_config_rejects_malformed_auth(auth_value, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NEO4J_AUTH", auth_value)

    with pytest.raises(ValueError, match="NEO4J_AUTH.*username/password"):
        get_neo4j_config()


def test_get_neo4j_config_rejects_empty_split_env_credentials(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NEO4J_USERNAME", "")
    monkeypatch.setenv("NEO4J_PASSWORD", "")

    with pytest.raises(
        ValueError, match="Neo4j username and password must be non-empty"
    ):
        get_neo4j_config()


def test_get_neo4j_config_rejects_empty_config_credentials(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".signal-graph"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        """
        [neo4j]
        username = ""
        password = ""
        """
    )

    with pytest.raises(
        ValueError, match="Neo4j username and password must be non-empty"
    ):
        get_neo4j_config()

import os
import subprocess
from pathlib import Path


def _assert_bind_mount_present(text: str, relative_path: str) -> None:
    mount_suffix = str(Path(relative_path))
    assert any(
        line.strip().startswith("source: ") and line.strip().endswith(mount_suffix)
        for line in text.splitlines()
    )


def test_docker_compose_declares_pinned_neo4j_image_and_bind_mounts():
    result = subprocess.run(
        ["docker", "compose", "config"],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "NEO4J_AUTH": "neo4j/password"},
    )
    assert result.returncode == 0
    text = result.stdout

    assert "neo4j:5.26.0-community" in text
    assert "NEO4J_AUTH: neo4j/password" in text
    assert "healthcheck:" in text
    assert "cypher-shell -u neo4j -p" in text
    assert "$${NEO4J_AUTH#*/}" in text
    assert "RETURN 1;" in text
    assert 'published: "7474"' in text
    assert 'published: "7687"' in text
    _assert_bind_mount_present(text, "infra/neo4j/data")
    _assert_bind_mount_present(text, "infra/neo4j/logs")
    _assert_bind_mount_present(text, "infra/neo4j/plugins")
    assert "target: /data" in text
    assert "target: /logs" in text
    assert "target: /plugins" in text

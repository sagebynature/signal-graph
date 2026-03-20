import os
from pathlib import Path
import subprocess


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
    assert f"source: {Path.cwd() / 'infra/neo4j/data'}" in text
    assert f"source: {Path.cwd() / 'infra/neo4j/logs'}" in text
    assert f"source: {Path.cwd() / 'infra/neo4j/plugins'}" in text
    assert "target: /data" in text
    assert "target: /logs" in text
    assert "target: /plugins" in text

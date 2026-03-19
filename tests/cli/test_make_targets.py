import subprocess
from pathlib import Path


def test_makefile_has_minimal_task_targets():
    assert Path("Makefile").exists()

    for target, expected in (
        ("test", "uv run pytest"),
        ("typecheck", "uv run ty check"),
        ("doctor", "uv run trade-graph doctor"),
        (
            "neo4j-up",
            "mkdir -p infra/neo4j/data infra/neo4j/logs infra/neo4j/plugins",
        ),
        ("neo4j-down", "docker compose stop neo4j"),
    ):
        result = subprocess.run(
            ["make", "-n", target],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert expected in result.stdout

    neo4j_up = subprocess.run(
        ["make", "-n", "neo4j-up"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "docker compose up -d neo4j" in neo4j_up.stdout

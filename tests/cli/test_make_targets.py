import subprocess
from pathlib import Path


def test_makefile_has_minimal_task_targets():
    assert Path("Makefile").exists()

    for target, expected in (
        ("test", "uv run pytest"),
        ("typecheck", "uv run ty check"),
        ("doctor", "uv run trade-graph doctor"),
    ):
        result = subprocess.run(
            ["make", "-n", target],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert expected in result.stdout

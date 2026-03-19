import shutil
import subprocess

def test_version_command_runs():
    command = shutil.which("trade-graph")
    assert command is not None

    result = subprocess.run(
        [command, "version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == "trade-graph 0.1.0\n"

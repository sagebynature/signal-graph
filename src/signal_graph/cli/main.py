from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from importlib.metadata import version as package_version
import sqlite3
from typing import ParamSpec

from neo4j.exceptions import DriverError, Neo4jError
import typer

from signal_graph.cli.doctor import doctor
from signal_graph.cli.explain import explain
from signal_graph.cli.fetch import fetch
from signal_graph.cli.ingest import ingest
from signal_graph.cli.init import init
from signal_graph.cli.normalize import normalize
from signal_graph.cli.rank import rank
from signal_graph.cli.research import research
from signal_graph.cli.submit import submit
from signal_graph.config import DEFAULT_PROJECT_DIR
from signal_graph.storage.sqlite import SqliteStore


app = typer.Typer(add_completion=False)
P = ParamSpec("P")

_PROJECT_DB_PATH = DEFAULT_PROJECT_DIR / "signal_graph.db"
_PROJECT_INIT_MESSAGE = "Project is not initialized. Run `signal-graph init` first."
_LOCAL_DATA_ERROR_MESSAGE = (
    "Unable to access local project data. Run `signal-graph init` first if needed."
)
_GRAPH_DB_ERROR_MESSAGE = (
    "Unable to reach the graph database. Check Neo4j settings and try again."
)


@app.callback()
def main() -> None:
    """signal-graph CLI."""


@app.command()
def version() -> None:
    print(f"signal-graph {package_version('signal-graph')}")


def _exit_command(message: str) -> None:
    typer.echo(message)
    raise typer.Exit(code=1)


def _ensure_project_initialized() -> None:
    if not DEFAULT_PROJECT_DIR.is_dir() or not _PROJECT_DB_PATH.is_file():
        _exit_command(_PROJECT_INIT_MESSAGE)

    try:
        store = SqliteStore(_PROJECT_DB_PATH)
        if not store.table_exists("raw_source_items"):
            _exit_command(_PROJECT_INIT_MESSAGE)
    except typer.Exit:
        raise
    except (OSError, sqlite3.Error):
        _exit_command(_LOCAL_DATA_ERROR_MESSAGE)


def _guard_command(
    command: Callable[P, None], *, requires_initialized_project: bool = False
) -> Callable[P, None]:
    @wraps(command)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            if requires_initialized_project:
                _ensure_project_initialized()
            command(*args, **kwargs)
        except typer.Exit:
            raise
        except ValueError as exc:
            _exit_command(str(exc))
        except (DriverError, Neo4jError):
            _exit_command(_GRAPH_DB_ERROR_MESSAGE)
        except (OSError, sqlite3.Error):
            _exit_command(_LOCAL_DATA_ERROR_MESSAGE)

    return wrapped


app.command()(doctor)
app.command()(_guard_command(explain, requires_initialized_project=True))
app.command()(fetch)
app.command()(_guard_command(ingest, requires_initialized_project=True))
app.command()(init)
app.command()(_guard_command(normalize, requires_initialized_project=True))
app.command()(_guard_command(rank, requires_initialized_project=True))
app.command()(_guard_command(research, requires_initialized_project=True))
app.command()(submit)


if __name__ == "__main__":
    app()

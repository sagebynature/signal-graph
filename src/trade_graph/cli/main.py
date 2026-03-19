from __future__ import annotations

from importlib.metadata import version as package_version

import typer


app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """trade-graph CLI."""


@app.command()
def version() -> None:
    print(f"trade-graph {package_version('trade-graph')}")


@app.command()
def doctor() -> None:
    print("doctor: pending")


if __name__ == "__main__":
    app()

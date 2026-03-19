from __future__ import annotations

from importlib.metadata import version as package_version

import typer

from trade_graph.cli.doctor import doctor
from trade_graph.cli.init import init


app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """trade-graph CLI."""


@app.command()
def version() -> None:
    print(f"trade-graph {package_version('trade-graph')}")


app.command()(doctor)
app.command()(init)


if __name__ == "__main__":
    app()

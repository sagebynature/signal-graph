from __future__ import annotations

from importlib.metadata import version as package_version

import typer

from trade_graph.cli.doctor import doctor
from trade_graph.cli.explain import explain
from trade_graph.cli.fetch import fetch
from trade_graph.cli.ingest import ingest
from trade_graph.cli.init import init
from trade_graph.cli.normalize import normalize
from trade_graph.cli.rank import rank
from trade_graph.cli.research import research
from trade_graph.cli.submit import submit


app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """trade-graph CLI."""


@app.command()
def version() -> None:
    print(f"trade-graph {package_version('trade-graph')}")


app.command()(doctor)
app.command()(explain)
app.command()(fetch)
app.command()(ingest)
app.command()(init)
app.command()(normalize)
app.command()(rank)
app.command()(research)
app.command()(submit)


if __name__ == "__main__":
    app()

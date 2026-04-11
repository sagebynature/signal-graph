from __future__ import annotations

import typer

from signal_graph.services.bootstrap import (
    build_bootstrap_contract,
    render_bootstrap_contract_markdown,
)


def bootstrap_describe(
    format: str = typer.Option(
        "json",
        "--format",
        help="Output format: json or markdown.",
    ),
) -> None:
    contract = build_bootstrap_contract()
    normalized = format.strip().lower()
    if normalized == "json":
        print(contract.model_dump_json(indent=2))
        return
    if normalized == "markdown":
        print(render_bootstrap_contract_markdown(contract))
        return
    raise ValueError("format must be one of: json, markdown")

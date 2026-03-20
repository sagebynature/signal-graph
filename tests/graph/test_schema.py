from __future__ import annotations

from signal_graph.graph.schema import REFERENCE_GRAPH_QUERIES


def test_reference_graph_seeds_multiple_supply_chain_and_etf_edges():
    assert any(
        "merge (tsmc)-[:supplies]->(amd)" in query.lower()
        for query in REFERENCE_GRAPH_QUERIES
    )
    assert any(
        "merge (soxx)-[:holds]->(nvda)" in query.lower()
        for query in REFERENCE_GRAPH_QUERIES
    )
    assert any(
        "merge (smh)-[:holds]->(amd)" in query.lower()
        for query in REFERENCE_GRAPH_QUERIES
    )

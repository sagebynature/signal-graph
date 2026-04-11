from __future__ import annotations

from signal_graph.graph.schema import REFERENCE_GRAPH_QUERIES, journal_signal_query


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


def test_journal_signal_query_links_signal_topology_dimensions():
    query = journal_signal_query().lower()

    assert "merge (s:journalsignal" in query
    assert "[:acted_by]" in query
    assert "[:who]" in query
    assert "[:what]" in query
    assert "[:where]" in query
    assert "[:how]" in query
    assert "[:why]" in query

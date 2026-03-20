from __future__ import annotations

from typing import Any, LiteralString, cast

from neo4j import GraphDatabase

from signal_graph.config import get_neo4j_config


class GraphClient:
    def __init__(self) -> None:
        config = get_neo4j_config()
        self.database = config["database"]
        self._driver = GraphDatabase.driver(
            config["uri"],
            auth=(config["username"], config["password"]),
        )
        self._driver.verify_connectivity()

    def run(self, query: str, params: dict[str, Any] | None = None) -> list[dict]:
        with self._driver.session(database=self.database) as session:
            return [
                record.data()
                for record in session.run(cast(LiteralString, query), params or {})
            ]

    def close(self) -> None:
        self._driver.close()

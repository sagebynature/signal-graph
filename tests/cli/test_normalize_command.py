from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from signal_graph.cli.main import app
from signal_graph.storage.sqlite import SqliteStore


def test_normalize_requires_initialized_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(app, ["normalize", "--raw-item", "raw-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_normalize_requires_database_file_in_initialized_project_dir(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    Path(".signal-graph").mkdir()

    runner = CliRunner()
    result = runner.invoke(app, ["normalize", "--raw-item", "raw-123"])

    assert result.exit_code == 1
    assert result.stdout.strip() == (
        "Project is not initialized. Run `signal-graph init` first."
    )


def test_normalize_help_describes_raw_item_identifier():
    runner = CliRunner()

    result = runner.invoke(app, ["normalize", "--help"])

    assert result.exit_code == 0
    assert "Raw source item id to normalize." in result.stdout


def test_normalize_creates_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    result = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])

    assert result.exit_code == 0
    assert "event_candidate_id" in result.stdout


def test_normalize_accepts_event_overrides(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    result = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "capex_cut",
            "--direction",
            "negative",
            "--primary-entity",
            "TSMC",
            "--secondary-entity",
            "SMH",
        ],
    )

    assert result.exit_code == 0
    event_candidate = json.loads(result.stdout)
    assert event_candidate["event_type"] == "capex_cut"
    assert event_candidate["direction"] == "negative"
    assert event_candidate["primary_entities"] == ["TSMC"]
    assert event_candidate["secondary_entities"] == ["SMH"]


def test_normalize_creates_distinct_event_candidates_for_matching_titles(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])

    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(app, ["normalize", "--raw-item", first_raw_item_id])
    second_normalize = runner.invoke(
        app, ["normalize", "--raw-item", second_raw_item_id]
    )

    assert first_normalize.exit_code == 0
    assert second_normalize.exit_code == 0
    first_event_candidate = json.loads(first_normalize.stdout)
    second_event_candidate = json.loads(second_normalize.stdout)
    assert (
        first_event_candidate["event_candidate_id"]
        != second_event_candidate["event_candidate_id"]
    )
    assert (
        first_event_candidate["dedupe_fingerprint"]
        == second_event_candidate["dedupe_fingerprint"]
    )
    assert first_event_candidate["source_item_ids"] == [first_raw_item_id]
    assert second_event_candidate["source_item_ids"] == [second_raw_item_id]

    database_path = Path(".signal-graph/signal_graph.db")
    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT event_candidate_id, dedupe_fingerprint, source_item_ids
            FROM event_candidates
            ORDER BY created_at
            """
        ).fetchall()

    assert rows == [
        (
            first_event_candidate["event_candidate_id"],
            first_event_candidate["dedupe_fingerprint"],
            json.dumps([first_raw_item_id]),
        ),
        (
            second_event_candidate["event_candidate_id"],
            second_event_candidate["dedupe_fingerprint"],
            json.dumps([second_raw_item_id]),
        ),
    ]


def test_normalize_is_idempotent_for_same_raw_item_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
        ],
    )
    second_normalize = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])

    assert first_normalize.exit_code == 0
    assert second_normalize.exit_code == 0

    first_event_candidate = json.loads(first_normalize.stdout)
    second_event_candidate = json.loads(second_normalize.stdout)
    assert (
        first_event_candidate["event_candidate_id"]
        == second_event_candidate["event_candidate_id"]
    )
    assert second_event_candidate["event_type"] == "supplier_disruption"
    assert second_event_candidate["direction"] == "negative"
    assert second_event_candidate["primary_entities"] == ["NVDA"]
    assert second_event_candidate["source_item_ids"] == [raw_item_id]

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        rows = connection.execute(
            """
            SELECT event_candidate_id, source_item_ids
            FROM event_candidates
            """
        ).fetchall()

    assert rows == [
        (
            first_event_candidate["event_candidate_id"],
            json.dumps([raw_item_id]),
        )
    ]


def test_normalize_rerun_for_same_raw_item_upgrades_metadata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    second_normalize = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
            "--secondary-entity",
            "SMH",
        ],
    )

    assert first_normalize.exit_code == 0
    assert second_normalize.exit_code == 0

    first_event_candidate = json.loads(first_normalize.stdout)
    second_event_candidate = json.loads(second_normalize.stdout)
    assert (
        first_event_candidate["event_candidate_id"]
        == second_event_candidate["event_candidate_id"]
    )
    assert second_event_candidate["event_type"] == "supplier_disruption"
    assert second_event_candidate["direction"] == "negative"
    assert second_event_candidate["primary_entities"] == ["NVDA"]
    assert second_event_candidate["secondary_entities"] == ["SMH"]
    assert second_event_candidate["source_item_ids"] == [raw_item_id]

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        row = connection.execute(
            """
            SELECT event_candidate_id, event_type, direction, primary_entities, secondary_entities
            FROM event_candidates
            WHERE event_candidate_id = ?
            """,
            (first_event_candidate["event_candidate_id"],),
        ).fetchone()

    assert row == (
        first_event_candidate["event_candidate_id"],
        "supplier_disruption",
        "negative",
        json.dumps(["NVDA"]),
        json.dumps(["SMH"]),
    )


def test_normalize_rerun_peels_raw_item_out_of_legacy_merged_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            first_raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
        ],
    )
    assert first_normalize.exit_code == 0
    legacy_event_candidate = json.loads(first_normalize.stdout)

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        connection.execute(
            """
            UPDATE event_candidates
            SET source_item_ids = ?
            WHERE event_candidate_id = ?
            """,
            (
                json.dumps([first_raw_item_id, second_raw_item_id]),
                legacy_event_candidate["event_candidate_id"],
            ),
        )
        connection.execute(
            """
            INSERT INTO event_candidate_source_items (raw_item_id, event_candidate_id)
            VALUES (?, ?)
            ON CONFLICT(raw_item_id) DO UPDATE SET event_candidate_id = excluded.event_candidate_id
            """,
            (second_raw_item_id, legacy_event_candidate["event_candidate_id"]),
        )

    repair_normalize = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            second_raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
            "--secondary-entity",
            "SMH",
        ],
    )
    repeat_normalize = runner.invoke(
        app, ["normalize", "--raw-item", second_raw_item_id]
    )

    assert repair_normalize.exit_code == 0
    assert repeat_normalize.exit_code == 0

    repaired_event_candidate = json.loads(repair_normalize.stdout)
    repeated_event_candidate = json.loads(repeat_normalize.stdout)
    assert (
        repaired_event_candidate["event_candidate_id"]
        != legacy_event_candidate["event_candidate_id"]
    )
    assert (
        repeated_event_candidate["event_candidate_id"]
        == repaired_event_candidate["event_candidate_id"]
    )
    assert repaired_event_candidate["source_item_ids"] == [second_raw_item_id]
    assert repeated_event_candidate["source_item_ids"] == [second_raw_item_id]
    assert repaired_event_candidate["secondary_entities"] == ["SMH"]

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        candidate_rows = connection.execute(
            """
            SELECT event_candidate_id, source_item_ids
            FROM event_candidates
            ORDER BY event_candidate_id
            """
        ).fetchall()
        lookup_rows = connection.execute(
            """
            SELECT raw_item_id, event_candidate_id
            FROM event_candidate_source_items
            ORDER BY raw_item_id
            """
        ).fetchall()

    assert candidate_rows == sorted(
        [
            (
                legacy_event_candidate["event_candidate_id"],
                json.dumps([first_raw_item_id]),
            ),
            (
                repaired_event_candidate["event_candidate_id"],
                json.dumps([second_raw_item_id]),
            ),
        ]
    )
    assert lookup_rows == sorted(
        [
            (first_raw_item_id, legacy_event_candidate["event_candidate_id"]),
            (second_raw_item_id, repaired_event_candidate["event_candidate_id"]),
        ]
    )


def test_normalize_returns_existing_candidate_when_insert_races_for_same_raw_item(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = json.loads(submit.stdout)["raw_item_id"]

    original_insert_event_candidate = SqliteStore.insert_event_candidate
    raced = False

    def racing_insert_event_candidate(self: SqliteStore, event_candidate):
        nonlocal raced
        if not raced:
            raced = True
            original_insert_event_candidate(
                self,
                event_candidate.model_copy(
                    update={"event_candidate_id": "evt-race-winner"}
                ),
            )
            raise sqlite3.IntegrityError(
                "UNIQUE constraint failed: event_candidate_source_items.raw_item_id"
            )
        return original_insert_event_candidate(self, event_candidate)

    monkeypatch.setattr(
        SqliteStore,
        "insert_event_candidate",
        racing_insert_event_candidate,
    )

    result = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
        ],
    )

    assert result.exit_code == 0
    event_candidate = json.loads(result.stdout)
    assert event_candidate["event_candidate_id"] == "evt-race-winner"
    assert event_candidate["event_type"] == "supplier_disruption"
    assert event_candidate["direction"] == "negative"
    assert event_candidate["primary_entities"] == ["NVDA"]

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        rows = connection.execute(
            """
            SELECT event_candidate_id, source_item_ids
            FROM event_candidates
            """
        ).fetchall()

    assert rows == [("evt-race-winner", json.dumps([raw_item_id]))]


def test_normalize_refuses_to_split_processed_legacy_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(app, ["normalize", "--raw-item", first_raw_item_id])
    assert first_normalize.exit_code == 0
    legacy_event_candidate = json.loads(first_normalize.stdout)

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        connection.execute(
            """
            UPDATE event_candidates
            SET source_item_ids = ?
            WHERE event_candidate_id = ?
            """,
            (
                json.dumps([first_raw_item_id, second_raw_item_id]),
                legacy_event_candidate["event_candidate_id"],
            ),
        )
        connection.execute(
            """
            INSERT INTO event_candidate_source_items (raw_item_id, event_candidate_id)
            VALUES (?, ?)
            ON CONFLICT(raw_item_id) DO UPDATE SET event_candidate_id = excluded.event_candidate_id
            """,
            (second_raw_item_id, legacy_event_candidate["event_candidate_id"]),
        )
        connection.execute(
            """
            INSERT INTO research_bundles (
                research_bundle_id,
                event_candidate_id,
                bundle_revision,
                supporting_documents,
                contradictions,
                entity_resolution_results,
                evidence_spans,
                research_confidence,
                research_notes,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"rb-{legacy_event_candidate['event_candidate_id']}",
                legacy_event_candidate["event_candidate_id"],
                1,
                json.dumps([]),
                json.dumps([]),
                None,
                json.dumps([]),
                0.0,
                None,
                None,
            ),
        )

    result = runner.invoke(app, ["normalize", "--raw-item", second_raw_item_id])

    assert result.exit_code == 1
    assert "processed legacy candidates cannot be auto-split" in result.stdout.lower()


def test_normalize_merges_overrides_when_concurrent_split_winner_already_exists(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    runner.invoke(app, ["init"])
    first_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    second_submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    first_raw_item_id = json.loads(first_submit.stdout)["raw_item_id"]
    second_raw_item_id = json.loads(second_submit.stdout)["raw_item_id"]

    first_normalize = runner.invoke(app, ["normalize", "--raw-item", first_raw_item_id])
    assert first_normalize.exit_code == 0
    legacy_event_candidate = json.loads(first_normalize.stdout)

    with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
        connection.execute(
            """
            UPDATE event_candidates
            SET source_item_ids = ?
            WHERE event_candidate_id = ?
            """,
            (
                json.dumps([first_raw_item_id, second_raw_item_id]),
                legacy_event_candidate["event_candidate_id"],
            ),
        )
        connection.execute(
            """
            INSERT INTO event_candidate_source_items (raw_item_id, event_candidate_id)
            VALUES (?, ?)
            ON CONFLICT(raw_item_id) DO UPDATE SET event_candidate_id = excluded.event_candidate_id
            """,
            (second_raw_item_id, legacy_event_candidate["event_candidate_id"]),
        )

    original_split = SqliteStore.split_legacy_event_candidate_for_raw_item
    raced = False

    def concurrent_winner_split(
        self: SqliteStore, existing_event_candidate, new_event_candidate, *, raw_item_id
    ):
        nonlocal raced
        if not raced:
            raced = True
            winner = new_event_candidate.model_copy(
                update={
                    "event_candidate_id": "evt-concurrent-winner",
                    "event_type": "unknown",
                    "direction": "unknown",
                    "primary_entities": [],
                    "secondary_entities": [],
                }
            )
            original_split(
                self,
                existing_event_candidate,
                winner,
                raw_item_id=raw_item_id,
            )
        with sqlite3.connect(Path(".signal-graph/signal_graph.db")) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT
                    ec.event_candidate_id,
                    ec.title,
                    ec.event_type,
                    ec.direction,
                    ec.primary_entities,
                    ec.dedupe_fingerprint,
                    ec.secondary_entities,
                    ec.source_item_ids,
                    ec.candidate_confidence,
                    ec.candidate_status,
                    ec.created_at
                FROM event_candidate_source_items AS ecsi
                JOIN event_candidates AS ec
                    ON ec.event_candidate_id = ecsi.event_candidate_id
                WHERE ecsi.raw_item_id = ?
                """,
                (raw_item_id,),
            ).fetchone()

        return SqliteStore._hydrate_event_candidate(self, row)

    monkeypatch.setattr(
        SqliteStore,
        "split_legacy_event_candidate_for_raw_item",
        concurrent_winner_split,
    )

    result = runner.invoke(
        app,
        [
            "normalize",
            "--raw-item",
            second_raw_item_id,
            "--event-type",
            "supplier_disruption",
            "--direction",
            "negative",
            "--primary-entity",
            "NVDA",
            "--secondary-entity",
            "SMH",
        ],
    )

    assert result.exit_code == 0
    event_candidate = json.loads(result.stdout)
    assert event_candidate["event_candidate_id"] == "evt-concurrent-winner"
    assert event_candidate["event_type"] == "supplier_disruption"
    assert event_candidate["direction"] == "negative"
    assert event_candidate["primary_entities"] == ["NVDA"]
    assert event_candidate["secondary_entities"] == ["SMH"]
    assert event_candidate["source_item_ids"] == [second_raw_item_id]

# Neo4j AI Trading Assistant Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI-first trading research toolkit that ingests events from premium, public, and manual sources into a canonical event pipeline, stores provenance locally, uses Neo4j for propagation reasoning, and produces ranked candidates plus evidence-backed trade memos.

**Architecture:** Implement a Python package with a `trade-graph` CLI, a local SQLite metadata store, a Neo4j graph client, and filesystem artifacts for cached documents and memo output. Use `uv` for environment and dependency management, `ty` for type checking, a top-level `Makefile` for common workflows, and a Docker-managed local Neo4j instance backed by bind-mounted host volumes. Keep the first cut terminal-native and agent-operable, with `SKILL.md` as the agent workflow contract and MCP deferred to a thin adapter later.

**Tech Stack:** Python 3.12, uv, Typer, Pydantic, SQLite, Neo4j Python driver, Rich, pytest, ty, Docker, Make

---

### Task 1: Scaffold The CLI Package

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `Makefile`
- Create: `src/trade_graph/__init__.py`
- Create: `src/trade_graph/cli/__init__.py`
- Create: `src/trade_graph/cli/main.py`
- Create: `tests/cli/test_version_command.py`
- Create: `tests/cli/test_make_targets.py`
- Create: `README.md`

**Step 1: Write the failing CLI test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_version_command_runs():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "trade-graph" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_version_command.py -v`
Expected: FAIL because `trade_graph.cli.main` does not exist yet

**Step 3: Write minimal package and CLI implementation**

```python
import typer

app = typer.Typer()


@app.command()
def version() -> None:
    print("trade-graph 0.1.0")
```

**Step 4: Add the console script entrypoint**

```toml
[project.scripts]
trade-graph = "trade_graph.cli.main:app"
```

**Step 5: Add `Makefile` targets for the default workflows**

```makefile
.PHONY: test typecheck lint doctor

test:
	uv run pytest -v

typecheck:
	uv run ty check

doctor:
	uv run trade-graph doctor
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/cli/test_version_command.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add pyproject.toml src tests README.md
git commit -m "feat: scaffold trade-graph cli package"
```

### Task 2: Add Config, Doctor, Init, And Toolchain Checks

**Files:**
- Create: `src/trade_graph/config.py`
- Create: `src/trade_graph/cli/doctor.py`
- Create: `src/trade_graph/cli/init.py`
- Create: `tests/cli/test_doctor_command.py`
- Create: `tests/cli/test_init_command.py`
- Modify: `src/trade_graph/cli/main.py`

**Step 1: Write the failing doctor test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_doctor_reports_missing_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "config" in result.stdout.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_doctor_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal config loader and doctor command**

```python
def get_default_config_path() -> Path:
    return Path(".trade-graph/config.toml")


def doctor() -> None:
    config_path = get_default_config_path()
    if config_path.exists():
        print("config: ok")
    else:
        print("config: missing")
```

**Step 4: Extend `doctor` to check `uv`, `ty`, Docker, and Neo4j config presence**

```python
checks = {
    "config": config_path.exists(),
    "docker": shutil.which("docker") is not None,
    "uv": shutil.which("uv") is not None,
    "ty": shutil.which("ty") is not None,
}
```

**Step 5: Add init command to create local directories**

```python
def init() -> None:
    Path(".trade-graph/cache").mkdir(parents=True, exist_ok=True)
    Path(".trade-graph/artifacts").mkdir(parents=True, exist_ok=True)
```

**Step 6: Run tests to verify they pass**

Run: `pytest tests/cli/test_doctor_command.py tests/cli/test_init_command.py -v`
Expected: PASS

**Step 7: Commit**

```bash
git add src tests
git commit -m "feat: add doctor and init commands"
```

### Task 3: Add Dockerized Neo4j Runtime With Bind Mounts

**Files:**
- Create: `docker-compose.yml`
- Create: `infra/neo4j/.gitkeep`
- Create: `infra/neo4j/data/.gitkeep`
- Create: `infra/neo4j/logs/.gitkeep`
- Create: `infra/neo4j/plugins/.gitkeep`
- Create: `tests/docs/test_docker_compose.py`
- Modify: `Makefile`
- Modify: `README.md`

**Step 1: Write the failing infrastructure test**

```python
from pathlib import Path


def test_docker_compose_declares_bind_mounts():
    text = Path("docker-compose.yml").read_text()
    assert "./infra/neo4j/data:/data" in text
    assert "./infra/neo4j/logs:/logs" in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_docker_compose.py -v`
Expected: FAIL because `docker-compose.yml` does not exist

**Step 3: Add the Docker Compose definition**

```yaml
services:
  neo4j:
    image: neo4j:5
    container_name: trade-graph-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - ./infra/neo4j/data:/data
      - ./infra/neo4j/logs:/logs
      - ./infra/neo4j/plugins:/plugins
```

**Step 4: Add Makefile helpers for Neo4j lifecycle**

```makefile
neo4j-up:
	docker compose up -d neo4j

neo4j-down:
	docker compose down
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/docs/test_docker_compose.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add docker-compose.yml infra Makefile README.md tests
git commit -m "feat: add dockerized neo4j runtime"
```

### Task 4: Create The Local Metadata Store

**Files:**
- Create: `src/trade_graph/storage/sqlite.py`
- Create: `src/trade_graph/storage/schema.sql`
- Create: `tests/storage/test_sqlite_store.py`
- Modify: `src/trade_graph/cli/init.py`

**Step 1: Write the failing storage test**

```python
from trade_graph.storage.sqlite import SqliteStore


def test_init_db_creates_source_items_table(tmp_path):
    store = SqliteStore(tmp_path / "trade_graph.db")
    store.init_db()
    assert store.table_exists("raw_source_items")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/storage/test_sqlite_store.py -v`
Expected: FAIL because `SqliteStore` does not exist

**Step 3: Write minimal SQLite store implementation**

```python
class SqliteStore:
    def __init__(self, path: Path):
        self.path = path

    def init_db(self) -> None:
        ...

    def table_exists(self, name: str) -> bool:
        ...
```

**Step 4: Add schema for canonical pipeline tables**

```sql
CREATE TABLE raw_source_items (...);
CREATE TABLE event_candidates (...);
CREATE TABLE research_bundles (...);
CREATE TABLE graph_events (...);
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/storage/test_sqlite_store.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add local sqlite metadata store"
```

### Task 5: Define Canonical Domain Models

**Files:**
- Create: `src/trade_graph/models/source.py`
- Create: `src/trade_graph/models/events.py`
- Create: `src/trade_graph/models/research.py`
- Create: `src/trade_graph/models/graph.py`
- Create: `tests/models/test_event_candidate.py`

**Step 1: Write the failing model test**

```python
from trade_graph.models.events import EventCandidate


def test_event_candidate_defaults():
    event = EventCandidate(
        event_candidate_id="evt-1",
        title="NVDA supplier disruption",
        event_type="supply_disruption",
        direction="negative",
        primary_entities=["NVDA"],
    )
    assert event.candidate_status == "pending"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_event_candidate.py -v`
Expected: FAIL because `EventCandidate` does not exist

**Step 3: Write minimal Pydantic models**

```python
class EventCandidate(BaseModel):
    event_candidate_id: str
    title: str
    event_type: str
    direction: str
    primary_entities: list[str]
    candidate_status: str = "pending"
```

**Step 4: Add graph ranking and memo response models**

```python
class RankedCandidate(BaseModel):
    ticker: str
    fast_reaction_score: float
    follow_through_score: float
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/models/test_event_candidate.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add canonical domain models"
```

### Task 6: Add Manual Submission And Raw Item Persistence

**Files:**
- Create: `src/trade_graph/cli/submit.py`
- Create: `src/trade_graph/services/raw_items.py`
- Create: `tests/cli/test_submit_command.py`
- Modify: `src/trade_graph/cli/main.py`

**Step 1: Write the failing submit test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_submit_stores_manual_raw_item(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])
    assert result.exit_code == 0
    assert "raw_item_id" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_submit_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal submit command**

```python
@app.command()
def submit(text: str) -> None:
    raw_item = create_manual_raw_item(text=text)
    print(raw_item.model_dump_json())
```

**Step 4: Persist submitted raw items to SQLite**

```python
def create_manual_raw_item(text: str) -> RawSourceItem:
    return RawSourceItem(
        raw_item_id=make_id("raw"),
        source_tier="tier3_manual",
        source_name="manual",
        raw_text=text,
    )
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_submit_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add manual event submission"
```

### Task 7: Add Normalization And Dedupe Commands

**Files:**
- Create: `src/trade_graph/cli/normalize.py`
- Create: `src/trade_graph/services/normalize.py`
- Create: `tests/cli/test_normalize_command.py`
- Modify: `src/trade_graph/models/events.py`
- Modify: `src/trade_graph/storage/sqlite.py`

**Step 1: Write the failing normalize test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_normalize_creates_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = submit.stdout.split('"raw_item_id":"')[1].split('"')[0]
    result = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    assert result.exit_code == 0
    assert "event_candidate_id" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_normalize_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal normalization logic**

```python
def normalize_raw_item(raw_item: RawSourceItem) -> EventCandidate:
    return EventCandidate(
        event_candidate_id=make_id("evt"),
        title=raw_item.raw_text,
        event_type="unknown",
        direction="unknown",
        primary_entities=[],
    )
```

**Step 4: Add basic dedupe fingerprinting**

```python
fingerprint = sha256(normalized_title.lower().encode()).hexdigest()
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_normalize_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add normalization and dedupe pipeline"
```

### Task 8: Add Public Connector And Premium Connector Interface

**Files:**
- Create: `src/trade_graph/connectors/base.py`
- Create: `src/trade_graph/connectors/public_web.py`
- Create: `src/trade_graph/connectors/premium_stub.py`
- Create: `src/trade_graph/cli/fetch.py`
- Create: `tests/cli/test_fetch_command.py`
- Modify: `src/trade_graph/cli/main.py`

**Step 1: Write the failing fetch test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_fetch_web_returns_raw_items(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["fetch", "--source", "web", "--query", "chip export restriction"])
    assert result.exit_code == 0
    assert "source_tier" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_fetch_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write connector interfaces and stub implementations**

```python
class BaseConnector(Protocol):
    def fetch(self, **kwargs) -> list[RawSourceItem]: ...
```

```python
class PremiumStubConnector:
    def fetch(self, **kwargs) -> list[RawSourceItem]:
        return []
```

**Step 4: Implement a deterministic public connector stub for tests**

```python
class PublicWebConnector:
    def fetch(self, query: str) -> list[RawSourceItem]:
        return [RawSourceItem(...)]
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_fetch_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add connector interfaces and fetch command"
```

### Task 9: Add Research Bundles And Provenance Rules

**Files:**
- Create: `src/trade_graph/cli/research.py`
- Create: `src/trade_graph/services/research.py`
- Create: `tests/cli/test_research_command.py`
- Modify: `src/trade_graph/models/research.py`
- Modify: `src/trade_graph/storage/sqlite.py`

**Step 1: Write the failing research test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_research_creates_bundle_for_event_candidate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = submit.stdout.split('"raw_item_id":"')[1].split('"')[0]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = normalized.stdout.split('"event_candidate_id":"')[1].split('"')[0]
    result = runner.invoke(app, ["research", "--event-candidate", event_candidate_id])
    assert result.exit_code == 0
    assert "research_bundle_id" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_research_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal research service**

```python
def build_research_bundle(event: EventCandidate) -> ResearchBundle:
    return ResearchBundle(
        research_bundle_id=make_id("rb"),
        event_candidate_id=event.event_candidate_id,
        supporting_documents=[],
        contradictions=[],
        research_confidence=0.0,
    )
```

**Step 4: Persist supporting evidence and contradictions**

```python
store.save_research_bundle(bundle)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_research_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add research bundle workflow"
```

### Task 10: Add Neo4j Schema And Ingest Command

**Files:**
- Create: `src/trade_graph/graph/client.py`
- Create: `src/trade_graph/graph/schema.py`
- Create: `src/trade_graph/cli/ingest.py`
- Create: `tests/cli/test_ingest_command.py`
- Modify: `src/trade_graph/storage/sqlite.py`

**Step 1: Write the failing ingest test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_ingest_creates_graph_event_record(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = submit.stdout.split('"raw_item_id":"')[1].split('"')[0]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = normalized.stdout.split('"event_candidate_id":"')[1].split('"')[0]
    runner.invoke(app, ["research", "--event-candidate", event_candidate_id])
    result = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    assert result.exit_code == 0
    assert "graph_event_id" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_ingest_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal Neo4j client and ingest service**

```python
class GraphClient:
    def run(self, query: str, params: dict | None = None) -> list[dict]:
        return []
```

```python
def ingest_event_candidate(event: EventCandidate, bundle: ResearchBundle) -> GraphEvent:
    return GraphEvent(graph_event_id=make_id("ge"), event_candidate_id=event.event_candidate_id)
```

**Step 4: Add graph constraints and relationship creation helpers**

```python
CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_ingest_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add neo4j ingest workflow"
```

### Task 11: Add Ranking And Timing Windows

**Files:**
- Create: `src/trade_graph/cli/rank.py`
- Create: `src/trade_graph/services/rank.py`
- Create: `src/trade_graph/services/timing.py`
- Create: `tests/cli/test_rank_command.py`
- Modify: `src/trade_graph/models/graph.py`

**Step 1: Write the failing ranking test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_rank_returns_candidates_with_scores(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    submit = runner.invoke(app, ["submit", "--text", "NVDA supplier disruption"])
    raw_item_id = submit.stdout.split('"raw_item_id":"')[1].split('"')[0]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = normalized.stdout.split('"event_candidate_id":"')[1].split('"')[0]
    runner.invoke(app, ["research", "--event-candidate", event_candidate_id])
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = ingested.stdout.split('"graph_event_id":"')[1].split('"')[0]
    result = runner.invoke(app, ["rank", "--event", graph_event_id])
    assert result.exit_code == 0
    assert "fast_reaction_score" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_rank_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal ranking service**

```python
def rank_event(graph_event_id: str) -> list[RankedCandidate]:
    return [
        RankedCandidate(
            ticker="SMH",
            fast_reaction_score=0.75,
            follow_through_score=0.40,
        )
    ]
```

**Step 4: Add timing window classification**

```python
def classify_timing(relationship_types: list[str]) -> str:
    if "MEMBER_OF" in relationship_types:
        return "immediate"
    return "short_drift"
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_rank_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add ranking and timing windows"
```

### Task 12: Add Explain Command And Markdown Memo Output

**Files:**
- Create: `src/trade_graph/cli/explain.py`
- Create: `src/trade_graph/services/explain.py`
- Create: `tests/cli/test_explain_command.py`
- Modify: `src/trade_graph/models/graph.py`

**Step 1: Write the failing explain test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_explain_outputs_memo_sections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["explain", "--event", "ge-1", "--candidate", "SMH"])
    assert result.exit_code == 0
    assert "Confirmed fact" in result.stdout
    assert "Graph implication" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/cli/test_explain_command.py -v`
Expected: FAIL because the command does not exist

**Step 3: Write minimal explanation service**

```python
def explain_candidate(graph_event_id: str, ticker: str) -> str:
    return "\n".join(
        [
            "Confirmed fact: Event was ingested from stored sources.",
            "Graph implication: Candidate is linked via stored relationship paths.",
            "Assistant inference: Timing window is immediate.",
        ]
    )
```

**Step 4: Write memo output to `.trade-graph/artifacts/`**

```python
artifact_path.write_text(memo_text)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/cli/test_explain_command.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src tests
git commit -m "feat: add explain command and memo artifacts"
```

### Task 13: Add `SKILL.md` And Agent Usage Docs

**Files:**
- Create: `skills/trade-graph/SKILL.md`
- Create: `docs/runbooks/agent-usage.md`
- Create: `tests/docs/test_skill_references.py`
- Modify: `README.md`

**Step 1: Write the failing documentation test**

```python
from pathlib import Path


def test_skill_mentions_provenance_and_command_order():
    text = Path("skills/trade-graph/SKILL.md").read_text()
    assert "provenance" in text.lower()
    assert "normalize" in text.lower()
    assert "research" in text.lower()
    assert "ingest" in text.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/docs/test_skill_references.py -v`
Expected: FAIL because the file does not exist

**Step 3: Write `SKILL.md` with explicit operating rules**

```md
- Never claim a causal path without a stored graph path and supporting sources.
- Distinguish confirmed fact, graph implication, and assistant inference.
- Prefer existing ingested events before live fetch.
- Use the command order: fetch/submit -> normalize -> research -> ingest -> rank -> explain.
```

**Step 4: Add agent runbook examples for Codex and Claude Code**

```md
trade-graph submit --text "TSMC cuts capex"
trade-graph normalize --raw-item raw-123
trade-graph research --event-candidate evt-123
trade-graph ingest --event-candidate evt-123
trade-graph rank --event ge-123
trade-graph explain --event ge-123 --candidate SMH
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/docs/test_skill_references.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add skills docs README.md tests
git commit -m "docs: add agent skill and usage guide"
```

### Task 14: Add End-To-End CLI Verification

**Files:**
- Create: `tests/e2e/test_manual_event_flow.py`
- Create: `docs/runbooks/local-development.md`
- Modify: `README.md`

**Step 1: Write the failing end-to-end test**

```python
from typer.testing import CliRunner

from trade_graph.cli.main import app


def test_manual_event_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    assert runner.invoke(app, ["init"]).exit_code == 0
    submit = runner.invoke(app, ["submit", "--text", "TSMC cuts capex"])
    raw_item_id = submit.stdout.split('"raw_item_id":"')[1].split('"')[0]
    normalized = runner.invoke(app, ["normalize", "--raw-item", raw_item_id])
    event_candidate_id = normalized.stdout.split('"event_candidate_id":"')[1].split('"')[0]
    assert runner.invoke(app, ["research", "--event-candidate", event_candidate_id]).exit_code == 0
    ingested = runner.invoke(app, ["ingest", "--event-candidate", event_candidate_id])
    graph_event_id = ingested.stdout.split('"graph_event_id":"')[1].split('"')[0]
    assert runner.invoke(app, ["rank", "--event", graph_event_id]).exit_code == 0
    assert runner.invoke(app, ["explain", "--event", graph_event_id, "--candidate", "SMH"]).exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/e2e/test_manual_event_flow.py -v`
Expected: FAIL until the full CLI flow is wired together

**Step 3: Add local development verification commands to docs**

```md
pytest -v
trade-graph doctor
trade-graph init
```

**Step 4: Run full verification**

Run: `uv run pytest -v`
Expected: PASS

**Step 5: Run type checks and smoke-test the CLI**

Run: `uv run ty check`
Expected: PASS

Run: `trade-graph version`
Expected: prints the package version

Run: `uv run trade-graph doctor`
Expected: prints config and environment checks

**Step 6: Commit**

```bash
git add docs README.md tests
git commit -m "test: verify end-to-end manual event workflow"
```

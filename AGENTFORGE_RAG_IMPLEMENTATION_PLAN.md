# AgentForge Transparent RAG Architecture and Implementation Plan

**Document type:** standalone architecture specification and implementation plan  
**Status:** proposed for external review; not approved for implementation  
**Date:** 2026-09-29  
**Supersedes:** all earlier AgentForge memory-backend architecture reasoning  
**Review state:** revised after external GPT review; five repair requests are incorporated and critically evaluated in §30  

> **Implementation gate:** Stop after review of this document. Do not create product code, database objects, packaging, or runtime infrastructure until the owner explicitly approves this architecture.

## 1. Goal and success definition

AgentForge is a machine-level developer tool that gives Claude, Codex, and future agents a shared, persistent, locally controlled knowledge base. A fresh session should retrieve what earlier agents learned, trace conclusions to evidence, distinguish measurements from hypotheses and accepted decisions, and avoid repeating known failures without loading entire project histories.

The project also has an educational goal: implement and understand the important RAG mechanics directly. AgentForge will expose ingestion, parsing, chunking, embeddings, lexical and vector retrieval, filtering, fusion, context budgeting, provenance, and evaluation. Focused libraries may implement generic primitives; no framework owns the retrieval pipeline.

V1 succeeds when all of the following are true:

- one installation and one PostgreSQL database serve all local projects;
- repositories carry only a stable project identity and project-specific configuration;
- default retrieval combines the current project with global knowledge and excludes other projects;
- documents, chunks, structured memories, embeddings, and retrieval indexes have distinct meanings;
- canonical text and memory history survive deletion and rebuilding of every derived index;
- lexical, semantic, and hybrid retrieval are individually observable and testable;
- a differently worded proposal retrieves a relevant prior failure near the top;
- knowledge written by one agent is retrievable by a fresh agent session;
- the normal task-start/resume workflow retrieves relevant history automatically rather than relying on the agent to remember a separate search command;
- context construction materially reduces tokens without dropping required evidence;
- the system remains understandable without reading a framework's internal pipeline.

## 2. Scope and constraints

### In V1

- Python package installed as a machine tool, exposing `agentctl`.
- Direct CLI-to-database execution against one local PostgreSQL instance.
- PostgreSQL relational storage, full-text search, and `pgvector`.
- Stable project UUID discovery and logical `global`/`project` scopes.
- Markdown and plain-text ingestion with structure-aware chunking.
- Replaceable embedding providers and model-versioned vectors.
- Explicit lexical, semantic, hybrid, and planning/anti-repeat retrieval profiles.
- Explicit structured-memory writes and immutable revision history.
- Provenance from every result to a document revision or explicit evidence reference.
- Context selection under a token budget.
- Dry-run bootstrap and idempotent incremental ingestion.
- Rebuild, evaluation, handoff, anti-repeat, scale, and recovery tests.

### Deliberately deferred

- Multi-user SaaS, RBAC, admin identities, project tokens, or hostile tenant isolation.
- A FastAPI service or always-running AgentForge daemon.
- Remote synchronization or multi-machine collaboration.
- Web UI.
- Knowledge graph.
- Automatic extraction of durable truth from every conversation.
- Autonomous prevention or blocking of agent actions.
- Learned ranker or advanced cross-encoder reranker.
- Cloud-hosted memory storage.
- Broad binary/PDF/Office/code parsing before Markdown/plain-text behavior is proven.

## 3. Architectural options considered

### Option A — direct Python pipeline over PostgreSQL (recommended)

`agentctl` discovers project context, opens PostgreSQL, runs explicit SQL and embedding calls, fuses candidates in application code, and renders results or context. PostgreSQL supplies transactions, metadata, full-text search, vectors, filtering, migrations, and backup in one locally controlled system.

**Benefits:** few moving parts; pipeline remains visible; no duplicate authorization/API layer; one transactional store; straightforward rebuilds and SQL inspection.  
**Costs:** each CLI invocation creates a process and database connection; local embedding model startup may be expensive unless the provider is an external local process; future non-CLI clients may justify a service later.

### Option B — local FastAPI service over PostgreSQL

A daemon owns connections, embedding models, and retrieval APIs while `agentctl` becomes a client.

**Benefits:** warm models, connection pooling, concurrent non-CLI clients, one place for scheduling.  
**Costs:** service lifecycle, ports, API compatibility, failure modes, logs, and duplication that do not serve the single-owner V1. It also makes a simple CLI/database system harder to learn.

**Decision:** defer. Add only after measurements show process startup/model loading dominates or a second client cannot reasonably invoke `agentctl`.

### Option C — embedded SQLite plus vector extension

An embedded database simplifies initial installation and removes a service.

**Benefits:** one-file storage and minimal operations.  
**Costs:** vector-extension portability and packaging, weaker alignment with the desired PostgreSQL learning path, likely later migration, and less uniform support for vector indexing plus full-text/metadata queries.

**Decision:** reject for V1. Use SQLite only in isolated unit tests where PostgreSQL behavior is not under test; all retrieval integration tests use PostgreSQL.

### Option D — LlamaIndex/Haystack/LangChain owns the pipeline

**Decision:** reject from the core. These frameworks may be benchmark adapters or implementation references. A high-level index/retriever call would hide the mechanics this project exists to teach.

## 4. System architecture

```text
managed repository
  .agent-team/config.toml       stable project UUID/name
             |
             v
agentctl process
  project discovery
  command/application services
  explicit ingestion and retrieval pipeline
             |
             +--------------------------+
             |                          |
             v                          v
local PostgreSQL + pgvector       EmbeddingProvider
  canonical sources/docs/memory     reference: local model
  derived chunks/FTS/vectors        replaceable provider boundary
  evaluation and job state
             |
             v
compact hits -> selective fetch -> context budget -> Claude/Codex
```

There is no V1 AgentForge server boundary. The operating-system user and PostgreSQL credentials are the trust boundary. Logical scope prevents accidental cross-project retrieval; it is not presented as hostile security isolation.

### Core modules and responsibilities

| Module | Responsibility | Must not do |
|---|---|---|
| `project` | Discover, initialize, and register stable projects | Infer identity from path/name |
| `storage` | SQLAlchemy mappings, repositories, transactions, migrations | Contain ranking policy |
| `ingest` | Discover sources, parse, normalize, hash, chunk, update manifest | Generate durable memories automatically |
| `embeddings` | Provider protocol, batching, generation registry, vector generation | Own canonical text |
| `retrieval` | Exact/lexical/vector candidate queries, filters, fusion, explanations | Assemble opaque prompts |
| `memory` | Explicit structured-memory commands, revisions, provenance, supersession | Treat agent prose as validated truth |
| `context` | Compact hits, selective fetch, deduplication, token budget | Replace deterministic task/rule context |
| `evaluation` | Datasets, metrics, anti-repeat/handoff/scale benchmarks | Tune against a single anecdotal query |
| `cli` | User/agent commands and stable output formats | Reimplement domain logic |

## 5. Canonical concepts and data ownership

### Document

A **document** is a logical source identity within a scope: for example `docs/research/matching.md`, `DECISIONS.md`, or an external research URL. It records where content came from and how AgentForge should treat it. A document is not a chunk and does not contain an embedding.

Each changed ingestion creates an immutable **document revision** containing the normalized source text (retaining Markdown syntax in V1), raw-content hash, normalizer version, capture time, source metadata, and current/superseded state. Keeping a reparsable text snapshot makes provenance and rebuilds independent of a file later changing or disappearing. Parser/chunker versions belong to derived processing records and chunks, so those layers can change without inventing a new source revision.

### Chunk

A **chunk** is a derived, retrievable fragment of one document revision. It has deterministic boundaries, text, heading path, line/character locators, ordinal, chunker version, and content hash. Chunks are stored for query speed but are rebuildable from canonical document revisions.

### Memory

A **memory** is durable learned knowledge deliberately written by an agent or human: note, observation, hypothesis, finding, failure, solution, decision, summary, or experiment result. It is not merely a copied chunk.

A stable memory identity points to immutable **memory revisions**. Updates append revisions. Supersession and archival are explicit lifecycle changes; old revisions remain inspectable. Memory evidence links back to document revisions, chunks as locators, commits, tasks, experiments, runs, or external sources.

Structured memory is an optional corpus type consumed by the same retrieval pipeline; it is not a prerequisite for RAG:

```text
                    RAG
                     |
                     v
          +-----------------------+
          | retrieval corpus      |
          |                       |
          | documents -> chunks   |
          | optional memories     |
          +-----------------------+
```

Phases 0–4 must demonstrate useful document retrieval before Phase 5 adds typed memory. The exact, lexical, semantic, fusion, fetch, and provenance machinery must work for document chunks alone. Adding memories extends the candidate corpus and lifecycle filters; it does not redefine RAG.

### Embedding

An **embedding** is a derived vector for a specific chunk or memory revision under a specific embedding model configuration. It is never canonical. It can be deleted and recreated from stored text. Multiple model generations may coexist during re-embedding.

### Retrieval index

A **retrieval index** is any derived acceleration structure: PostgreSQL `tsvector`, GIN index, pgvector HNSW/IVFFlat index, exact-literal helper index, or cached retrieval statistic. Indexes may be dropped without losing knowledge.

### Canonical versus derived

| Canonical | Derived/rebuildable |
|---|---|
| projects and scope identity | chunks and their boundary metadata |
| document identities and immutable document revisions | `tsvector` values and GIN indexes |
| memory identities and immutable memory revisions | embeddings and vector indexes |
| evidence/provenance links | excerpts and ranking explanations |
| lifecycle/supersession relations | retrieval caches and evaluation run results |
| version-controlled evaluation queries and expected sources (outside the DB) | generated synthetic scale corpus and evaluation run reports |

Chunks are intentionally classified as derived even though they are persisted. A chunk ID must therefore never be the only durable evidence reference; provenance includes its document revision and stable locator.

## 6. PostgreSQL model

### Scope representation

Use a two-column invariant rather than magic namespace strings:

```text
scope_kind = 'global'  -> project_id IS NULL
scope_kind = 'project' -> project_id IS NOT NULL
```

A check constraint enforces the pair. Default project retrieval always applies:

```sql
scope_kind = 'global' OR project_id = :current_project_id
```

Explicit all-project search is deferred. No per-project credentials or row-level security are needed in V1.

### Tables

This is the complete target V1 schema, not the Phase 1 migration. Tables are introduced only by the phase that first needs them: canonical document identity in Phase 1, chunks in Phase 2, embedding generations/vectors in Phase 3, and structured memory/evidence in Phase 5.

| Table | Canonical? | Purpose and key fields |
|---|:---:|---|
| `projects` | yes | `id UUID`, mutable name, timestamps, last-seen path; project ID comes from repository config |
| `documents` | yes | stable logical source: scope, source kind, canonical URI, title, inclusion policy, active flag, last successful full-corpus scan; identity is independent of discovery path |
| `document_revisions` | yes | immutable normalized/reparsable source text, raw SHA-256, normalizer version, source metadata, captured time, current flag |
| `chunks` | derived | document revision, ordinal, text, heading path, line/character range, token count, parser/chunker versions, hash |
| `memories` | yes | stable memory identity, scope, current revision ID, created time |
| `memory_revisions` | yes | immutable type, state, title, body, valid time, author/agent, reason, revision number |
| `memory_relations` | yes | typed links such as `supersedes`, `contradicts`, `supports`, `derived_from` |
| `evidence_refs` | yes | memory revision, optional document revision, stable source URI, stable locator JSON, excerpt hash, relation; never depends on a chunk FK |
| `embedding_generations` | yes config | immutable generation ID, provider/model ID, dimensions, normalization, distance metric, provider/config fingerprint, lifecycle/active state |
| `chunk_embeddings` | derived | chunk FK, generation ID, dimensions, untyped `vector`, text hash, created time |
| `memory_embeddings` | derived | memory-revision FK, generation ID, dimensions, untyped `vector`, text hash, created time |
| `ingestion_runs` | operational | corpus scope/project, mode, configured-root policy fingerprint, counts, parser/chunker versions, errors, start/end |

Evaluation definitions stay as version-controlled JSONL/YAML fixtures and reports as versioned JSON/Markdown artifacts. They do not need database tables in V1; this keeps the production schema focused and makes benchmark changes reviewable in Git.

### Vector dimensions and model changes

Use pgvector's dimensionless `vector` storage with an explicit `dimensions` column and immutable generation registry. A composite foreign key `(generation_id, dimensions)` references a unique pair on `embedding_generations`, and a database check enforces `vector_dims(embedding) = dimensions`. Provider registration rejects dimensions unsupported by the installed pgvector type/version. V1 begins with exact cosine scans filtered by active `generation_id` because the target scale is thousands of items and exact search is easier to validate. When benchmarks justify approximate search, create a generation-specific partial expression index such as a cast to `vector(768)` for the active generation. Index DDL is derived from the registry and recorded in a migration/maintenance operation.

Re-embedding writes a complete second generation beside the active generation. Search switches the active generation only after counts, dimensions, text hashes, and a retrieval evaluation pass. The previous generation is retained until rollback is no longer needed.

### Transaction rules

- A document revision and its chunk/FTS projection become current only in the same transaction that retires its predecessor. Embedding availability is tracked separately and never blocks canonical/lexical activation.
- A memory update appends a revision and changes the current pointer atomically using an expected revision number.
- Supersession atomically writes the new/updated memory revision and relation.
- An embedding batch is resumable; partial rows never make an embedding generation active.
- Only a completed full scan across the entire configured root set for one `(scope, project)` corpus may deactivate documents absent from that discovered union. Discovery deduplicates overlapping roots by canonical URI before applying changes. Explicit-path/additive ingestion never marks anything missing. Deactivation never deletes revisions or evidence.

## 7. Project discovery and machine configuration

`agentctl` walks from the current directory toward the filesystem root and uses the nearest `.agent-team/config.toml`. The committed configuration contains at least:

```toml
project_id = "<uuid>"
project_name = "registar-by-luk"

[memory]
enabled = true
```

`agentctl project init` generates the UUID once, refuses to overwrite an existing identity, writes configuration atomically, and registers/updates the project in the central database. Moving or renaming the repository changes only `projects.last_seen_path`. A duplicated repository with the same ID is treated as the same project until an explicit future `project rekey`; V1 reports the duplicate path rather than guessing.

Machine configuration uses the platform's user configuration directory and contains the PostgreSQL DSN plus embedding-provider/model selection. The V1 reference provider is a small local model so the default learning path and stored corpus remain locally controlled. `EmbeddingProvider` is not architecturally local-only: a later provider may be local-process, remote, or hosted without changing canonical data or retrieval logic. Any non-local provider must require explicit opt-in, display that source text leaves the machine, pass data-egress tests, and keep credentials in environment/keychain-backed configuration rather than project config or the database.

## 8. Ingestion and chunking

### Ingestion pipeline

```text
discover -> classify/include -> read bytes -> hash -> normalize/store revision
         -> parse -> deterministic chunks -> lexical index -> activate revision
         -> generate missing embeddings independently/resumably
```

The dry run stops before database writes and reports discovered, included, excluded, duplicate, changed, missing, and estimated-chunk counts by source kind.

Document identity is `(scope, project_id, canonical_uri)` and is independent of how the source was discovered. V1 reads configured roots with include/exclude rules, canonicalizes discovered URIs, and deduplicates their union before applying ingestion. A successful full-corpus scan records its policy fingerprint and may mark documents absent from that union inactive. An interrupted scan or explicit `ingest PATHS...` run is additive and may never infer absence. This handles overlapping roots without a source-membership subsystem.

SHA-256 of raw bytes detects content changes. The canonical revision fingerprint also contains `normalizer_version` and normalized-text SHA-256: changing the normalizer creates a new canonical revision even when raw bytes are unchanged. Parser and chunker version changes rebuild derived chunks without inventing a source revision. Ingestion is idempotent: the same raw bytes, normalizer, and processing versions produce no new canonical revision or duplicate chunks. Embedding failure leaves a current lexical-searchable revision plus explicit semantic-index staleness; it does not roll back canonical ingestion.

Independent per-root reconciliation and persisted many-to-many source membership are deferred. Add them only if real corpora require roots with separate ownership/lifecycles that cannot safely be scanned as one configured union.

### V1 parsers

- Markdown: preserve heading hierarchy, fenced-code blocks, lists, tables as blocks, and source line ranges.
- Plain text: preserve paragraphs and line ranges.
- Existing structured memory: never reparsed as a document.

HTML, PDF, Office, notebooks, and source-code AST parsing are deferred until evaluation data proves need.

### Structure-aware chunking defaults

- split first at Markdown heading/semantic block boundaries;
- target about 600 model tokens, hard maximum 900;
- combine adjacent tiny blocks within the same section until roughly 120 tokens;
- split oversized sections at paragraph/list/code-block boundaries;
- use 80-token overlap only when an oversized semantic section must be divided;
- never detach a code fence, table, or list item halfway unless it individually exceeds the maximum;
- prepend/store heading path as metadata, not duplicated canonical content;
- hash normalized chunk text plus locator and chunker version for deterministic identity.

These are initial testable defaults, not truths. Phase 9 evaluation may change them through versioned configuration.

## 9. Transparent retrieval pipeline

### Query contract

A `SearchRequest` contains query text, current project ID, retrieval profile, allowed types/states/source kinds, top-k, per-scope candidate quotas, active embedding generation, historical flag, and optional token budget. Scope is resolved by project discovery, not inferred by the embedding provider.

### Candidate lanes

1. **Exact/literal lane:** stable IDs, filenames, symbols, commit hashes, and quoted error fragments. V1 uses indexed metadata equality/prefix checks plus escaped literal substring matching; add `pg_trgm` only after measurement.
2. **Lexical lane:** PostgreSQL full-text search over current chunks and current memory revisions using the `simple` text-search configuration to preserve technical terms. Use `websearch_to_tsquery` for ordinary input, rank with `ts_rank_cd`, and expose the generated query/rank.
3. **Semantic lane:** embed the query with the provider for the active generation, filter by generation and scope, and compute cosine distance against chunk/memory vectors.
4. **Planning lanes (added in Phase 5):** for `profile=planning`, run additional filtered lexical/semantic candidates over validated failures and current decisions. This is how significant proposals deliberately check known mistakes. Phase 4 implements only generic exact/lexical/semantic retrieval; it must not guess Phase 5 lifecycle semantics.

Each lane collects a bounded quota of project candidates and global candidates so neither scope can exhaust collection capacity. Those candidates are then merged and sorted by their common lane score into **one** lexical rank list and **one** semantic rank list before fusion. Scope is not a separate RRF lane: it is diagnostic metadata, not an independent vote. Exact score ties prefer the current project only as a deterministic tie-break.

All metadata/status/scope filters are applied inside candidate SQL, before top-N truncation.

### Fusion

V1 uses Reciprocal Rank Fusion because lexical and vector scores are not calibrated to the same scale:

```text
RRF(canonical_target) = sum(1 / (k + rank_in_lane)), default k = 60
```

Exact matches receive their own ranked lane rather than an unexplained numeric boost. Candidate quotas, scope, lane ranks, RRF contributions, filters, and final rank are returned in an explanation object. Weighted score fusion is retained as an evaluation alternative, not the default. No learned reranker is included.

Fusion operates on canonical retrieval targets, not raw rows: a target is a document revision or a memory revision, with its stable logical document/memory ID also returned. Within each lane, chunk rows are first collapsed by document revision: the highest-scoring chunk supplies the document revision's lane score, up to three strongest passage locators are retained, and only then are lane ranks assigned. A memory revision is already one target. RRF combines the resulting per-target ranks. Final presentation may merge passages but never sum multiple chunks from the same document revision, preventing long documents from receiving a multi-hit boost or crowding a lane. Superseded/rejected/archived memories and inactive document revisions are excluded unless `historical=true`.

### Search response

Compact search hits include:

```text
canonical id
kind: document | memory
title
memory type/state when applicable
scope/project
final rank and per-lane rank contribution
short bounded excerpt
source URI and stable locator
current/superseded indicator
fetch handle
```

The fetch handle resolves to canonical text/evidence; it does not expose a chunk as the only source of truth.

## 10. Structured memory and provenance

Agents write durable knowledge explicitly through `agentctl memory add` or a structured stdin/JSON input. Required fields are type, state, title, body, scope, and at least one evidence reference for `finding`, `failure`, `solution`, `decision`, or `experiment_result`. `note`, `observation`, and `hypothesis` may lack evidence but remain clearly labelled.

Default new states:

- note -> `draft`;
- observation -> `observed`;
- hypothesis -> `proposed`;
- finding/failure/solution/decision/experiment result -> `proposed` unless the caller explicitly records validation evidence.

Validation, rejection, supersession, and archival append revisions with actor, timestamp, and reason. Destructive delete is reserved for erroneous/private data and is not the normal lifecycle.

Evidence references store a stable source URI and locator even when a document revision/chunk exists. A retrieval result can therefore show the memory, then fetch the exact document revision and location that supported it. Chunk rebuilds cannot break provenance.

## 11. Context builder and anti-repeat behavior

The context builder combines two inputs:

```text
mandatory deterministic context supplied by the caller
+
retrieved historical knowledge selected by AgentForge
```

It never retrieves or replaces current acceptance criteria, current task text, hard rules, or active constraints unless the caller explicitly supplies them as deterministic input.

Context construction is two-stage:

1. `search` returns compact ranked metadata/excerpts.
2. `context` fetches selected canonical fragments, groups duplicate evidence, and greedily fills the historical-context budget while reserving configured capacity for failures and decisions under the planning profile.

Selection is deterministic and explained: rank, required/reserved category, token cost, duplicate group, and inclusion/exclusion reason. Token counting is provider-specific when an exact tokenizer exists and conservative otherwise.

To reduce repeated mistakes, the normal task-start/resume workflow invokes the planning profile before significant implementation or experimentation. That profile reserves up to three relevant validated-failure/current-decision slots before filling with general results. Direct diagnostic queries remain available. This is automatic context attachment, not an autonomous blocker, and its effectiveness is measured by the anti-repeat benchmark.

## 12. Public Python interfaces

```python
class EmbeddingProvider(Protocol):
    @property
    def model_id(self) -> str: ...
    @property
    def dimensions(self) -> int: ...
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...

class DocumentParser(Protocol):
    @property
    def parser_id(self) -> str: ...
    def parse(self, source: SourceBytes) -> ParsedDocument: ...

class Chunker(Protocol):
    @property
    def chunker_id(self) -> str: ...
    def split(self, document: ParsedDocument) -> Sequence[ChunkDraft]: ...

class Retriever(Protocol):
    def search(self, request: SearchRequest) -> SearchResponse: ...

class ContextBuilder(Protocol):
    def build(self, request: ContextRequest) -> BuiltContext: ...
```

Application services expose `initialize_project`, `ingest`, `add_memory`, `revise_memory`, `search`, `fetch`, `build_context`, `rebuild`, and `evaluate`. CLI commands call these services; SQLAlchemy models and provider clients never leak into CLI or domain types.

## 13. Proposed CLI surface

CLI syntax is provisional until the existing `agentctl` code is available for inspection. Required capabilities are:

```text
agentctl project init
agentctl project status

agentctl memory add|get|search|related|update|validate|reject|supersede|archive|history
agentctl memory ingest [PATHS...] [--dry-run]
agentctl memory bootstrap [--dry-run]
agentctl memory rebuild chunks|lexical|embeddings|all
agentctl memory status

agentctl context query "..." [--profile default|planning] [--budget TOKENS]
agentctl context task TASK_ID

agentctl memory eval run DATASET
agentctl system status|doctor
```

Every read command supports human-readable and JSON output. Writes accept non-interactive structured input so agents do not scrape prompts.

`context task` defaults to the `planning` retrieval profile because its purpose is to prepare significant work; free-form `context query` defaults to `default` unless the caller explicitly requests planning behavior.

## 14. Package and file structure

```text
pyproject.toml
alembic.ini
src/agentforge/
  cli.py
  config.py
  domain/
    documents.py
    memory.py
    retrieval.py
    provenance.py
  project/
    discovery.py
    initialization.py
  storage/
    db.py
    models.py
    repositories.py
    migrations/
  ingest/
    discovery.py
    parsers.py
    chunking.py
    service.py
  embeddings/
    base.py
    registry.py
    local.py
    openai_compatible.py
    service.py
  retrieval/
    exact.py
    lexical.py
    semantic.py
    fusion.py
    service.py
  memory/
    service.py
  context/
    tokens.py
    builder.py
  evaluation/
    datasets.py
    metrics.py
    runner.py
tests/
  unit/
  integration/
  acceptance/
  fixtures/
docs/
  architecture/
  evaluation/
```

The split follows responsibilities, not framework layers. SQL is kept close to each retrieval lane so a reader can see exactly how candidates are produced.

## 15. Implementation workflow and ownership

The plan is sequenced so every phase produces a reviewable, testable capability. Tasks marked **main-session** contain a compatibility or architectural decision that must remain with the coordinator. Tasks marked **delegated** are decision-complete implementation packages suitable for a bounded worker after approval. In a shared checkout, only one actor edits at a time.

### Required contract for every delegated task

When converting any delegated task below into a worker prompt, copy the task's objective/files/interfaces/tests/exit criteria and the following contract verbatim or equivalently:

- **Source-of-truth precedence:** approved version of this plan; then existing repository tests/public interfaces; then current official documentation for the pinned dependency. Stop on conflict rather than choosing silently.
- **Decided assumptions:** direct synchronous CLI architecture, one local PostgreSQL database, single-owner logical scope, canonical/derived boundaries in §§5–6, and no full RAG framework types in core.
- **Scope/exclusions:** edit only listed task files and directly required migration/test fixtures; do not redesign architecture, add dependencies, change unrelated CLI behavior, or start later phases.
- **Authority boundary:** the worker may implement the specified interface and tests but may not change data ownership, lifecycle semantics, trust boundaries, ranking policy, public schemas, or acceptance thresholds.
- **Deliverables:** listed files, migrations where named, focused tests, and a compact evidence report.
- **Required evidence:** failing test before implementation where applicable; focused passing tests; relevant real-PostgreSQL integration result; exact diff inspection.
- **Acceptance:** the task's exit criteria plus no regressions in previously completed phases.
- **Output/read-back:** conclusion; changed files/symbols; tests/commands and result; deviations; unresolved risks; exact question needing coordinator judgment. No raw logs unless a failure requires them.
- **Stop conditions:** missing required source/interface; contradictory plan/code evidence; unplanned architecture, data-integrity, concurrency, privacy, or migration decision; acceptance requiring broader scope.

This common contract plus each task's explicit details is the complete delegation contract. A task must return to the main session whenever the contract cannot be satisfied as written.

Global implementation constraints:

- Python 3.12 or newer unless the existing `agentctl` package proves a lower compatible floor is mandatory.
- PostgreSQL and the pgvector extension are the only V1 persistence/search services.
- Use synchronous SQLAlchemy 2.1 + psycopg 3 and synchronous core/provider protocols for CLI code; do not introduce async execution without a measured need.
- Every schema change uses Alembic; pgvector/FTS/index DDL is reviewed explicitly rather than trusted to autogenerate.
- Every feature follows test-first development with unit tests plus real-PostgreSQL integration tests where SQL behavior matters.
- No full RAG framework type crosses a core interface.
- JSON output is versioned and deterministic so coding agents can consume it.
- Each task is committed separately only after its focused checks pass; the workspace must first be placed under the intended Git repository.

### Review focus across all phases

1. A moved repository retains its project scope, while two paths with the same project UUID produce a clear diagnostic rather than duplicate memory.
2. Reprocessing unchanged content, restarting interrupted embedding work, and rebuilding indexes never duplicate canonical records.
3. Superseded/rejected knowledge stays inspectable but is absent from default retrieval.
4. Exact technical identifiers remain retrievable even when semantic similarity is weak.
5. Deleting all derived chunks, `tsvector` values, vectors, and indexes can be followed by a complete rebuild from canonical rows.

## 16. Phase 0 — disposable RAG learning slice

### Goal

Make the essential RAG mechanism visible end to end before building AgentForge infrastructure: one Markdown file becomes explicit chunks and vectors in disposable PostgreSQL tables, and a query returns the five nearest chunks with distances and source ranges.

This is a learning experiment, not an early production layer. It must not create final domain models, migrations, `agentctl` commands, framework abstractions, memory types, project/global scoping, hybrid retrieval, or reusable application code.

### Interfaces produced

- No production interface.
- A standalone command under `spikes/rag_learning/` with `ingest FILE` and `search QUERY --top-k 5` operations.
- A short learning report recording observed chunk boundaries, vectors, SQL, distances, useful/missed results, latency, and questions that change later phase decisions.

### Task 0.1 — transparent one-document semantic slice (**main-session**)

**Files:** create isolated files only under `spikes/rag_learning/`; use a disposable PostgreSQL schema/table names that cannot collide with `agentforge`.  
**Tests first:** deterministic fixture chunk boundaries; one row per chunk; vector dimensions match provider output; a fixed query returns five ordered chunks with distance and line range; re-ingest replaces the disposable file rows without duplicates.  
**Implementation:** write the shortest explicit sequence that remains inspectable: read Markdown, split with a deliberately simple documented rule, call the reference local embedding provider, insert pgvector rows, embed the query, execute cosine-distance SQL, print results. No LlamaIndex/Haystack/LangChain and no production imports.  
**Exit criteria:** the owner can inspect every transformation and run a query such as “why did brightness matching fail?”; the learning report explains at least one retrieval success, one miss or limitation, and which assumptions should or should not enter Phase 2/3.

### Task 0.2 — disposal gate (**main-session**)

**Evidence:** compare the spike against the Phase 1–4 contracts and identify observations only; do not copy its schema, types, or simplistic chunker into production by default.  
**Exit criteria:** before Phase 1, the owner chooses whether to retain the isolated spike as an educational artifact or delete it. In either case it remains outside the installed package and production test suite.

### Phase 0 risks

- A toy result can create false confidence; it teaches mechanics but does not validate provenance, hybrid quality, lifecycle, scope, or scale.
- “Disposable” code can become accidental production code; directory isolation and the disposal gate prevent that path.
- Model download/setup can dominate the lesson; pin one small reference model and record its license/hardware behavior without making it an architectural requirement.

## 17. Phase 1 — foundation

### Goal

Create the standalone package boundary, machine/project configuration, project discovery, PostgreSQL connection, migrations, and canonical storage model without any retrieval behavior.

### Interfaces produced

- `AppSettings`, `ProjectConfig`, and `ProjectContext`.
- `discover_project(start: Path) -> ProjectContext`.
- `initialize_project(path: Path, name: str) -> ProjectContext`.
- `Database.transaction()` and schema-version/health operations.
- Repository interfaces for projects and document revisions. Chunk tables arrive in Phase 2, embedding-generation tables in Phase 3, and memory tables in Phase 5.

### Task 1.1 — existing `agentctl` compatibility audit (**main-session**)

**Depends on:** access to the actual existing `agentctl` source, which is not present in this workspace.  
**Deliverable:** `docs/architecture/agentctl-compatibility.md`; confirm package root, CLI framework, configuration conventions, task identifiers, output conventions, reusable project discovery, and any existing memory data/types/states/lifecycle semantics. The type/state enum proposed in this plan remains provisional until this audit.  
**Stop condition:** if existing interfaces contradict this plan, update this document and obtain review rather than creating a parallel CLI.

### Task 1.2 — package, settings, and project discovery (**delegated**)

**Files:** create `pyproject.toml`, `src/agentforge/config.py`, `src/agentforge/project/discovery.py`, `src/agentforge/project/initialization.py`, `tests/unit/project/test_discovery.py`, `tests/unit/project/test_initialization.py`.  
**Tests first:** nearest-config discovery; repository move; missing/malformed config; atomic initialization; refusal to replace an existing ID; duplicate UUID/path diagnostic; TOML round-trip.  
**Implementation:** use `tomllib` for reads, an explicit small TOML writer for known keys, `platformdirs` or existing project convention for machine config, UUIDv4 for new identities.  
**Verification:** focused pytest; CLI-free domain tests use temporary directories.  
**Exit evidence:** the same project UUID is returned before and after moving the fixture tree.

### Task 1.3 — PostgreSQL lifecycle and initial migrations (**delegated**)

**Files:** create `src/agentforge/storage/db.py`, `src/agentforge/storage/models.py`, `src/agentforge/storage/repositories.py`, `alembic.ini`, migration environment, initial migration, `tests/integration/storage/test_schema.py`.  
**Tests first:** clean upgrade; downgrade/upgrade in a disposable database; required extensions; constraints on global/project scope; immutable document revision uniqueness; foreign keys; schema version reporting; absence of premature chunk, embedding, and memory tables.  
**Implementation:** create only the Phase 1 canonical foundation (`projects`, `documents`, `document_revisions`, and `ingestion_runs`) in a controlled `agentforge` schema; enable `vector` so environment failure is diagnosed early; use typed columns for common filters, JSONB only for extensible locators/metadata, and qualify schema names. Later phases own their derived and memory migrations.  
**Verification:** migration from empty database and schema introspection against real PostgreSQL.  
**Exit evidence:** all Phase 1 canonical tables and constraints exist; no chunk, retrieval index, embedding-generation, or structured-memory schema is required to read canonical document rows.

### Task 1.4 — project registration and health commands (**delegated**)

**Files:** create/update `src/agentforge/cli.py`, `src/agentforge/project/service.py`, `tests/acceptance/test_project_commands.py`, `tests/integration/test_health.py`.  
**Tests first:** `project init/status` human and JSON output; last-seen path update; database unavailable; pgvector missing/wrong version; incompatible schema version.  
**Implementation:** reuse the existing CLI framework discovered by Task 1.1; otherwise use stdlib `argparse`.  
**Exit criteria:** a temporary project can initialize, move, rediscover, and report one stable database registration.

### Phase 1 risks

- Existing `agentctl` may live in another repository or use incompatible configuration keys.
- `uv tool` installation does not install PostgreSQL/pgvector; system setup must be documented and diagnosed, not silently attempted.
- ORM convenience can obscure constraints; migrations and generated SQL require review.

## 18. Phase 2 — ingestion

### Goal

Persist immutable document revisions and generate deterministic, provenance-rich chunks through an explicit, idempotent pipeline.

### Interfaces produced

- `DocumentParser.parse(SourceBytes) -> ParsedDocument`.
- `Chunker.split(ParsedDocument) -> Sequence[ChunkDraft]`.
- `IngestionService.plan(request) -> IngestionPlan`.
- `IngestionService.apply(plan) -> IngestionReport`.

### Task 2.1 — source/document domain and parser fixtures (**delegated**)

**Files:** create `src/agentforge/domain/documents.py`, `src/agentforge/ingest/parsers.py`, representative fixtures under `tests/fixtures/documents/`, and `tests/unit/ingest/test_parsers.py`.  
**Tests first:** Markdown headings, paragraphs, lists, tables, code fences, Unicode, empty files, CRLF/LF normalization, and exact source line ranges; plain-text paragraph/line handling.  
**Implementation:** use `markdown-it-py` only to expose syntax tokens; AgentForge converts tokens into its own `ParsedBlock` model and owns all chunk decisions.  
**Exit criteria:** parsed blocks preserve text, order, structure, and source locators without framework-specific objects.

### Task 2.2 — deterministic structure-aware chunker (**delegated**)

**Files:** create the chunk-table migration, `src/agentforge/ingest/chunking.py`, `tests/unit/ingest/test_chunking.py`, `tests/unit/ingest/test_chunking_properties.py`.  
**Tests first:** default size targets; no split code fence/table/list item unless oversized; heading paths; bounded overlap only for forced splits; stable IDs/hashes; no empty chunks; reconstructable ordered coverage; version change invalidation.  
**Implementation:** implement the §8 policy explicitly against AgentForge blocks; tokenizer is injected.  
**Exit criteria:** identical input/config produces byte-identical chunk manifests, and every chunk maps to a document revision locator.

### Task 2.3 — source discovery, hashing, manifest, and dry run (**delegated**)

**Files:** create `src/agentforge/ingest/discovery.py`, `src/agentforge/ingest/service.py`, `tests/unit/ingest/test_discovery.py`, `tests/integration/ingest/test_incremental.py`.  
**Tests first:** include/exclude patterns; symlinks; duplicate discovery through overlapping configured roots; unchanged/changed/missing files; normalizer versus parser/chunker version changes; full configured-corpus scan versus additive explicit paths; changed root-policy fingerprint; interrupted run; dry run makes zero writes.  
**Implementation:** raw SHA-256 plus normalizer/version controls canonical revisions; plan and apply are separate; discovery canonicalizes and deduplicates the union of configured roots; activation is transactional after all chunks exist; only a successful full-corpus scan reconciles missing documents for its `(scope, project)` corpus; additive paths never deactivate.  
**Exit criteria:** two identical runs create one document revision/chunk set; overlapping roots produce one document; changed bytes or normalizer creates one new revision; parser/chunker-only change rebuilds derived chunks; a source absent from a successful full configured-root union becomes inactive with history intact; interrupted and partial-path runs never deactivate unrelated sources.

### Task 2.4 — ingestion CLI and diagnostics (**delegated**)

**Files:** update `src/agentforge/cli.py`; create `tests/acceptance/test_ingest_commands.py`.  
**Tests first:** dry-run counts, JSON schema, partial error reporting, explicit paths, default configured roots, non-project/global ingestion.  
**Exit criteria:** an agent can inspect exactly what will be stored before applying it.

### Phase 2 risks

- Token counts vary by model; chunker tests must pin a deterministic test tokenizer.
- Markdown source maps may be imperfect around tables/code; locators must be tested against real fixtures.
- Storing normalized full text duplicates repository data, but it is necessary for durable provenance and rebuilds.

## 19. Phase 3 — embeddings and vector retrieval

### Goal

Add a replaceable embedding boundary, model-versioned vector persistence, resumable re-embedding, and transparent exact semantic retrieval.

### Interfaces produced

- `EmbeddingProvider` from §12.
- `Tokenizer` with exact/estimated result metadata.
- `EmbeddingService.embed_missing(generation_id, batch_size) -> JobReport`.
- `SemanticRetriever.search(request) -> Sequence[LaneHit]`.

### Task 3.1 — provider contract and deterministic test provider (**delegated**)

**Files:** create the embedding-generation registry migration, `src/agentforge/embeddings/base.py`, `src/agentforge/embeddings/registry.py`, `src/agentforge/context/tokens.py`, `tests/unit/embeddings/test_contract.py`.  
**Tests first:** batching/order preservation; dimensions; empty input; transient/permanent errors; model/config fingerprint; deterministic fake vectors; exact versus estimated token counts.  
**Exit criteria:** all embedding work can be tested without downloading or calling a real model.

### Task 3.2 — reference local provider and provider portability proof (**delegated**)

**Files:** create `src/agentforge/embeddings/local.py` and provider contract tests.  
**Tests first:** local model identity/dimensions, batch consistency, normalization policy, unavailable model, model/config fingerprint, unsupported dimensions, and a second fake adapter proving that no local-runtime type crosses the provider boundary.  
**Implementation:** `sentence-transformers` is the optional reference `local-embeddings` extra and the default V1 learning configuration. The provider protocol permits future local-process or remote adapters; implementing a remote adapter is deferred until explicit opt-in, egress disclosure, secret handling, and privacy tests are approved.  
**Exit criteria:** changing provider does not change canonical document/memory rows or retrieval interfaces; the reference workflow runs locally, while the architecture remains provider-neutral.

### Task 3.3 — vector persistence and resumable generation (**delegated**)

**Files:** create `src/agentforge/embeddings/service.py`, vector migration, `tests/integration/embeddings/test_persistence.py`.  
**Tests first:** generation/model/dimension constraints; database vector-dimension check; text-hash staleness; duplicate prevention; partial batch resume; coexistence of two generations; inactive generation cannot be searched; rollback to old generation.  
**Exit criteria:** delete/recreate embeddings from canonical text and obtain complete matching counts.

### Task 3.4 — exact semantic retrieval (**delegated**)

**Files:** create `src/agentforge/retrieval/semantic.py`, `tests/integration/retrieval/test_semantic.py`.  
**Tests first:** cosine ordering; current project + global filter; other-project exclusion; type/state/source filters; deterministic tie-break; absent query model; historical mode.  
**Implementation:** start with exact pgvector search; return distance, rank, model ID, and SQL-relevant diagnostics.  
**Exit criteria:** semantic lane passes the curated paraphrase fixtures without an ANN index.

### Phase 3 risks

- Model downloads and licenses vary independently from the provider library.
- A dimensionless vector column requires a mandatory model predicate and careful index DDL later.
- A provider can be unavailable, slow, dimensionally incompatible, or identify itself incorrectly; diagnostics verify health, model identity, dimensions, and whether data leaves the machine. Non-local providers require explicit opt-in rather than an architectural ban.

## 20. Phase 4 — lexical and hybrid retrieval

### Goal

Implement exact technical lookup, PostgreSQL full-text candidates, scope/status filters, explainable RRF fusion, and optional measured ANN acceleration.

### Interfaces produced

- `ExactRetriever`, `LexicalRetriever`, `SemanticRetriever` returning common `LaneHit` values.
- `fuse_rrf(lanes, k=60) -> Sequence[FusedHit]`.
- `Retriever.search(SearchRequest) -> SearchResponse`.

### Task 4.1 — exact and full-text schema/query lane (**delegated**)

**Files:** create `src/agentforge/retrieval/exact.py`, `src/agentforge/retrieval/lexical.py`, FTS migration, `tests/integration/retrieval/test_exact.py`, `tests/integration/retrieval/test_lexical.py`.  
**Tests first:** IDs (`T032`, `EXP-0041`), filenames, class/function names, error strings, commit hashes, punctuation, Unicode, project+global scope, state filters, deterministic ties.  
**Implementation:** stored/generated `tsvector` with explicit `simple` configuration and GIN; `websearch_to_tsquery` or `plainto_tsquery` selected by tested behavior; literal lane handles what tokenization cannot.  
**Exit criteria:** exact identifiers are reliably top-ranked and lexical query diagnostics expose config/query/rank.

### Task 4.2 — transparent RRF and deduplication (**delegated**)

**Files:** create `src/agentforge/retrieval/fusion.py`, `tests/unit/retrieval/test_fusion.py`.  
**Tests first:** per-scope quota merge by common score; chunk collapse before rank assignment; best-chunk score with three retained passages; long-document no multi-hit boost; missing lanes; duplicate target IDs; ties; deterministic ordering; configurable `k`; exact-lane contribution; no score normalization.  
**Implementation:** pure AgentForge code; each lane yields one ranked entry per canonical document/memory target, and each fused output includes per-lane rank and contribution.  
**Exit criteria:** hand-calculated fixtures equal implementation results exactly.

### Task 4.3 — generic search orchestration (**delegated**)

**Files:** create `src/agentforge/retrieval/service.py`, `tests/integration/retrieval/test_hybrid.py`, `tests/acceptance/test_planning_retrieval.py`.  
**Tests first:** scope quotas occur before the common lane rank; candidate filters occur before lane limits; project+global merge; cross-project exclusion; compact result schema; bounded excerpts; document chunks collapse before lane ranking; up to three passage locators retained; no multi-hit document boost.  
**Exit criteria:** exact, lexical, and semantic lanes produce one explainable per-target rank list and deterministic RRF results over document chunks while no structured-memory tables exist. At this point AgentForge is already a usable document RAG system.

### Task 4.4 — ANN decision benchmark (**main-session**)

**Files:** create `docs/evaluation/vector-index-decision.md`, benchmark fixtures/scripts under `tests/benchmarks/`.  
**Tests/evidence:** compare exact search with HNSW at representative 10k, 100k, and—if feasible—1M derived vectors; measure recall against exact, p50/p95 latency, build time, disk, and filtered-scope behavior using `EXPLAIN (ANALYZE, BUFFERS)`.  
**Decision:** add a model-specific partial HNSW expression index only if the measured benefit is material and recall meets the acceptance threshold. Do not add IVFFlat in V1 without separate evidence.  
**Exit criteria:** documented keep-exact or add-HNSW decision with reproducible commands and pinned pgvector version.

### Phase 4 risks

- PostgreSQL FTS tokenization does not preserve every code/error literal; the exact lane is mandatory.
- ANN filtering can reduce recall because filtering happens after candidate scan; benchmark scoped queries explicitly.
- Hybrid success can be overfit to one query; Phase 9 owns aggregate evaluation.

## 21. Phase 5 — structured agent memory

### Goal

Optionally extend the already functioning document RAG corpus with typed reusable knowledge written by agents and humans, including evidence, revisions, validation, supersession, archive, history, and retrieval indexing. Phase 5 must reuse the Phase 4 retriever rather than create a separate memory-search architecture.

### Interfaces produced

- `MemoryDraft`, `MemoryRevision`, `EvidenceRef`, and `MemoryRelation`.
- `MemoryService.add/revise/transition/supersede/history/related`.
- Structured JSON input/output schemas for agent use.

### Task 5.1 — memory invariants and repository (**delegated**)

**Files:** create the memory/evidence Alembic migration, `src/agentforge/domain/memory.py`, `src/agentforge/domain/provenance.py`, `src/agentforge/memory/service.py`, `tests/unit/memory/test_invariants.py`, `tests/integration/memory/test_revisions.py`.  
**Tests first:** migration from the complete Phase 4 schema; document-only search unchanged before and after migration; allowed type/state combinations; evidence requirement; immutable revisions; optimistic revision conflict; state transition rules; global/project scope; actor/timestamp/reason; history order.  
**Exit criteria:** no update mutates an old revision, and concurrent stale writes fail clearly.

### Task 5.2 — provenance and source fetch (**delegated**)

**Files:** extend memory/storage repositories; create `tests/integration/memory/test_provenance.py`.  
**Tests first:** evidence to exact document revision/line range; external URI; commit/task/experiment locator; chunk rebuild; source deletion; excerpt-hash mismatch; multiple supporting/contradicting sources.  
**Exit criteria:** every required memory type can be traced to immutable evidence after chunks and embeddings are deleted/rebuilt.

### Task 5.3 — lifecycle, supersession, and history commands (**delegated**)

**Files:** update CLI and service; create `tests/acceptance/test_memory_lifecycle.py`.  
**Tests first:** add, revise, validate, reject, supersede, archive, history, destructive-delete refusal/default, JSON round-trip, default search exclusion, historical inclusion.  
**Exit criteria:** current decision retrieval returns only the active decision by default while the prior decision and reason remain fetchable.

### Task 5.4 — memory embeddings and retrieval parity (**delegated**)

**Files:** extend embedding targets and retrieval queries; create `tests/integration/memory/test_memory_retrieval.py`.  
**Tests first:** new revision invalidates old derived embedding; failure/hypothesis labels preserved; chunk and memory candidates fuse without ID collision; evidence included in compact hit; planning profile adds validated-failure/current-decision lanes; default/historical state behavior; EXP-0034 paraphrase top-three result; `memory related` returns explicit relations before similarity fallback, excludes the seed, applies project/global and lifecycle filters, and produces deterministic hybrid fallback ordering.  
**Implementation:** add the planning profile only after Task 5.1 locks lifecycle semantics. `memory related ID` returns explicit `supports`/`contradicts`/`supersedes` relations first, then hybrid-similar memories/documents using the current revision's title/body as the explained query; it excludes the seed memory itself.  
**Exit criteria:** typed memory and document chunks share retrieval without sharing canonical tables or identities, and the known failure ranks top three under planning profile.

### Phase 5 risks

- Too many lifecycle states could burden agents; keep transition rules explicit and CLI defaults safe.
- Requiring evidence for every note/hypothesis would discourage use; require it only for stronger claims.
- Automatic extraction would blur fact and hypothesis, so it remains deferred.

## 22. Phase 6 — context builder

### Goal

Turn compact ranked hits into deterministic, provenance-rich historical context under a token budget while keeping mandatory task/rule context separate.

### Interfaces produced

- `Tokenizer.count(text) -> TokenCount(count, exact, tokenizer_id)`.
- `ContextRequest` with mandatory context, selected/fetchable hits, historical budget, and profile.
- `BuiltContext` with ordered sections, provenance, token accounting, and exclusion reasons.

### Task 6.1 — tokenizers and budget accounting (**delegated**)

**Files:** create `src/agentforge/context/tokens.py`, `tests/unit/context/test_tokens.py`.  
**Tests first:** exact adapter, conservative estimator, Unicode/code, empty text, over-budget mandatory content, accounting totals, tokenizer identity.  
**Implementation:** optional `tiktoken`/Hugging Face adapters; never claim exact Claude/Codex tokens without the matching tokenizer.  
**Exit criteria:** every built context reports exact or estimated counts honestly.

### Task 6.2 — selective fetch, grouping, and deterministic selection (**delegated**)

**Files:** create `src/agentforge/context/builder.py`, `tests/unit/context/test_builder.py`, `tests/integration/context/test_fetch.py`.  
**Tests first:** document-only context with memory schema/feature disabled; group redundant chunks; fetch exact locators; greedy budget; planning-profile failure/decision reservation when memory is enabled; current before historical; stable ordering; oversized single evidence; missing source fallback.  
**Exit criteria:** identical request/database state produces identical context and inclusion explanations.

### Task 6.3 — context CLI and agent-readable format (**delegated**)

**Files:** update CLI; create `tests/acceptance/test_context_commands.py`.  
**Tests first:** search-only compact results; explicit fetch; `context query`; mandatory context kept separate; JSON schema; budget errors; citations/source handles.  
**Exit criteria:** an agent can first inspect hits and then request a bounded context without loading full documents.

### Phase 6 risks

- Greedy selection may be suboptimal; prefer transparent behavior until evaluation proves a more complex selector is warranted.
- Model-specific tokenizers change; record tokenizer ID and treat estimates conservatively.
- Mandatory context can itself exceed budget; report rather than truncate silently.

## 23. Phase 7 — `agentctl` integration

### Goal

Expose stable non-interactive commands and integrate memory retrieval into the existing agent coordination workflow without forcing a daemon or framework runtime.

### Interfaces produced

- Versioned CLI JSON schemas.
- Exit-code/error taxonomy.
- A task-start context envelope containing mandatory task data plus automatically retrieved planning context.
- Agent operating guidance for when to search, use planning mode, fetch evidence, and write memory.

### Task 7.1 — command integration and compatibility (**main-session**)

**Depends on:** Phase 1 compatibility audit and access to existing task/inbox/report interfaces.  
**Files:** update actual `agentctl` command registration; create `docs/agent-memory-workflow.md`.  
**Tests:** existing commands remain behaviorally compatible; memory subcommands do not shadow/rename existing syntax; current task identifiers resolve deterministically; identify the normal task-start/resume hook that can attach planning context without requiring a separate search command.  
**Exit criteria:** full pre-existing CLI test suite plus memory command suite passes, and the integration point for automatic task context is documented before Task 7.4 proceeds.

### Task 7.2 — structured input/output and error contract (**delegated**)

**Files:** create `src/agentforge/cli_schemas.py`, `tests/acceptance/test_cli_json.py`.  
**Tests first:** schema version; stdin JSON for writes; stable IDs; no prompts in agent mode; database/provider errors; partial ingestion report; nonzero exit codes; human output remains readable.  
**Exit criteria:** Claude/Codex can call every V1 workflow without parsing prose.

### Task 7.3 — system status and rebuild orchestration (**delegated**)

**Files:** create `src/agentforge/maintenance.py`, CLI wiring, `tests/acceptance/test_maintenance_commands.py`, `tests/integration/test_rebuild.py`.  
**Tests first:** status counts/staleness; chunks-only, lexical-only, embedding-only, and full rebuild; dry run; interruption/resume; model generation switch; canonical checksum unchanged.  
**Exit criteria:** delete all derived rows/indexes, rebuild, and reproduce expected retrieval while canonical table hashes remain unchanged.

### Task 7.4 — automatic task-lifecycle retrieval and acceptance test (**delegated**)

**Files:** extend the actual task-start/resume service and JSON schema discovered by Task 7.1; create `tests/acceptance/test_agent_workflow.py`. The illustrative command is `agentctl task start T032`, but existing CLI syntax takes precedence.  
**Tests first:** task start/resume invokes the planning profile automatically; output keeps mandatory task/acceptance/rule context distinct from retrieved history; known failures, current decisions, related experiments, provenance handles, and token accounting are present; retrieval failure returns mandatory task data plus `historical_context.status=unavailable` and a conspicuous diagnostic; `--require-memory` makes the same failure fail closed; low-level memory search remains available for diagnostics.  
**Scenario:** Agent A records an evidenced failure and decision, exits; a fresh process representing Agent B receives only project config and a new task and uses the normal task lifecycle—without remembering or issuing a separate memory-search command.  
**Implementation decision:** V1 defaults to fail-open because a memory outage must not hide the current task or break existing coordination. Automation that requires the memory guard may pass `--require-memory` for fail-closed behavior.  
**Exit criteria:** the ordinary task-start/resume response includes bounded relevant history and the required failure/decision with no process-local state, copied transcript, or manual retrieval step.

### Task 7.5 — canonical backup and restore proof (**delegated**)

**Files:** create `docs/operations/backup-restore.md`, `tests/acceptance/test_backup_restore.py`, and only if approved a thin CLI wrapper around `pg_dump`/`pg_restore`.  
**Tests first:** backup a populated disposable database; restore into a clean database; verify canonical row/content hashes and memory history; drop derived state in the restored database; rebuild and reproduce evaluation fixtures.  
**Exit criteria:** both database-loss recovery and derived-index rebuild are proven separately. The documentation names PostgreSQL/tool versions and does not imply that reindexing replaces backups.

### Phase 7 risks

- Existing CLI conventions are unknown until its repository is available.
- Machine-tool output becomes a compatibility surface; version JSON early.
- Agents can still bypass `agentctl` entirely, but the normal `agentctl` task-start/resume path automatically retrieves planning context; forgetting a separate memory-search command is no longer the default failure mode.

## 24. Phase 8 — Registar bootstrap

### Goal

Use Registar as the first real corpus through an auditable, reversible selection and ingestion process rather than indexing the repository indiscriminately.

### Interfaces produced

- Bootstrap policy/manifest format.
- `BootstrapPlan` with source classification and reasons.
- Reviewed initial durable-memory import file.

### Task 8.1 — source inventory and policy (**main-session**)

**Depends on:** access to the Registar repository and owner review.  
**Files in Registar:** create a bootstrap manifest under its agreed `.agent-team/` path; do not modify product runtime.  
**Work:** inventory `CLAUDE.md`, `AGENTS.md`, `.agent-team/`, docs research/analysis/validation, current state, decisions, reports, and tasks. Classify each source as mandatory deterministic, high-value retrieval, historical, superseded, noise, or exclude, with a reason and precedence.  
**Exit criteria:** owner reviews the dry-run manifest before ingestion.

### Task 8.2 — bootstrap dry-run and idempotent ingestion (**delegated**)

**Files:** create `src/agentforge/ingest/bootstrap.py`, `tests/acceptance/test_bootstrap.py`.  
**Tests first:** manifest precedence, chatter exclusion (`OK`, `ACK`, `Continue`, `Noted`), duplicates, superseded sources, estimates, no writes in dry run, re-run idempotency, changed-file update.  
**Exit criteria:** dry-run totals reconcile with applied totals and no excluded content appears in search.

### Task 8.3 — initial durable knowledge review/import (**main-session**)

**Work:** derive candidate failure/decision/experiment memories from authoritative Registar evidence into a reviewable structured file; a human approves each entry before import. No autonomous extraction writes validated truth.  
**Tests/evidence:** every strong memory has a resolvable source; hypotheses remain proposed; superseded decisions are linked; duplicate claims are consolidated.  
**Exit criteria:** approved memory set is imported and all provenance fetches succeed.

### Phase 8 risks

- Source precedence may be contradictory; the owner must adjudicate.
- Historical chatter can dominate semantic results unless excluded.
- Bootstrap extraction can manufacture certainty; human review is mandatory.

## 25. Phase 9 — evaluation

### Goal

Measure retrieval quality, anti-repeat behavior, handoff, scale, latency, token reduction, and rebuild correctness before declaring V1 successful.

### Interfaces produced

- Versioned JSONL/YAML evaluation dataset schema.
- Metric calculator and reproducible evaluation report.
- Optional benchmark adapters for external frameworks that consume the same pre-chunked corpus.

### Task 9.1 — curated retrieval benchmark (**main-session**)

**Files:** create `tests/fixtures/evaluation/registar-v1.jsonl`, `src/agentforge/evaluation/datasets.py`, `src/agentforge/evaluation/metrics.py`, tests for metrics.  
**Dataset:** each query records project, profile, expected canonical source/memory IDs, must-not-return IDs, top-k, and budget. Include all example questions from the brief plus exact identifiers, paraphrases, current/superseded decisions, code/error strings, and project/global mixes.  
**Metrics:** recall@k, precision@k, MRR, expected rank, irrelevant hits, token volume, and latency; nDCG only when graded relevance labels exist.  
**Tests first:** hand-calculated metric fixtures; malformed/duplicate dataset entries; deterministic reports; held-out query separation; must-not-return violations; absent expected source; environment/config fingerprint capture.  
**Initial exit thresholds:** expected-source recall@10 >= 0.90; every current-decision query excludes superseded hits by default; every exact-ID query ranks the exact target first. Threshold changes require documented evidence, not silent tuning.

### Task 9.2 — mandatory anti-repeat benchmark (**delegated**)

**Files:** create `tests/acceptance/test_anti_repeat_benchmark.py` and benchmark dataset cases.  
**Scenario:** store failed approach X, reason Y, conditions Z; query later with multiple differently worded proposals.  
**Exit criteria:** the validated failure is top three for every planning-profile paraphrase and its evidence/reason is fetchable. Any miss fails AgentForge's primary purpose.

### Task 9.3 — mandatory fresh-agent handoff (**delegated**)

**Files:** create `tests/acceptance/test_fresh_agent_handoff.py`.  
**Scenario:** Claude-like process writes what was tried, failure reason, and controlling decision; process exits; a clean Codex-like process receives only the current task/project config and retrieves them.  
**Exit criteria:** required failure and decision appear within budget without transcript or cache reuse.

### Task 9.4 — scale, latency, and filter recall (**delegated**)

**Files:** create deterministic synthetic-corpus generator and `tests/benchmarks/test_scale.py`.  
**Corpus:** at least 10,000 chunks plus 2,000 structured memories across global and multiple projects, with planted relevant/contradictory/superseded items.  
**Measure:** ingest/rebuild time, database size, exact versus ANN recall, p50/p95 search latency, scoped-filter recall, and context-build latency on a named reference machine.  
**Initial exit target:** p95 hybrid search under 500 ms at 10k chunks on the reference machine, with no loss of required recall; report rather than conceal hardware/model effects.

### Task 9.5 — token-reduction and rebuild/recovery benchmark (**delegated**)

**Files:** create `tests/benchmarks/test_context_efficiency.py`, `tests/acceptance/test_disaster_rebuild.py`.  
**Compare:** full relevant documents/manual history versus compact search + selected source fragments.  
**Exit criteria:** at least 70% historical-context token reduction on the curated tasks while preserving all required expected evidence; complete retrieval recovery after dropping derived chunks/FTS/vectors/indexes and rebuilding from canonical rows.

### Task 9.6 — framework reference benchmarks (**delegated, optional after native baseline**)

**Files:** create isolated benchmark adapters under `benchmarks/frameworks/`; they are not runtime dependencies.  
**Work:** feed the same pre-chunked corpus, metadata, embedding model, and queries to Haystack (primary comparison), LlamaIndex, and a thin LangChain retriever adapter where practical. Compare dense, lexical, hybrid, provenance preservation, latency, and token selection.  
**Exit criteria:** publish differences without changing AgentForge architecture merely to match framework APIs.

### Phase 9 risks

- Curated queries can overfit; keep a held-out set and add every real miss as a regression.
- Synthetic scale proves mechanics, not real relevance; Registar remains the semantic test.
- Latency targets are hardware/model dependent; always record environment and configuration fingerprints.

## 26. Library choices and educational boundary

| Library/primitive | Decision | Why | What AgentForge still implements explicitly |
|---|---|---|---|
| Python stdlib `argparse` | default if existing CLI has no framework | Dependency-free and transparent | Command semantics, JSON schemas, domain services |
| Existing CLI framework | preserve if already used | Avoids gratuitous migration | Same as above; framework stays presentation-only |
| Pydantic + `pydantic-settings` | use for settings and boundary DTO validation | Clear validation and environment/config handling | Domain rules, retrieval, persistence, ranking |
| SQLAlchemy 2.1 | use selectively | Mappings, transactions, PostgreSQL types; Python >=3.11 | Retrieval SQL remains visible; no generic vector-store abstraction |
| psycopg 3 | use synchronous driver | One local CLI does not need async complexity | Transaction boundaries, batching, retry policy |
| Alembic | use | Auditable schema migrations | Hand-written pgvector/FTS/index/data migrations |
| PostgreSQL FTS | use | Local lexical search and metadata filtering in the same DB | Exact lane, query construction, ranking, diagnostics |
| pgvector + pgvector-python | use | Local vector storage/operators with SQLAlchemy integration | Model registry, vector lifecycle, candidate query, recall tests |
| `markdown-it-py` | use | Exposes Markdown syntax/structure without deciding chunks | Parsed-block mapping, chunking, locators, tests |
| `sentence-transformers` | reference V1 provider | Practical small local embeddings for the default learning path | Provider contract, batching, storage, model generations |
| OpenAI-compatible embedding client | adapter deferred, boundary supported | Proves the provider design need not assume process locality, but can enable accidental remote data egress | Add only after explicit opt-in policy, disclosure, secrets handling, and egress tests |
| `tiktoken` / Hugging Face tokenizers | optional adapters | Exact only for matching model/tokenizer | Tokenizer protocol, conservative estimates, budget policy |
| NumPy | optional provider/test dependency | Efficient vector array handling | Core types remain provider-neutral sequences |
| pytest | use | Direct unit/integration/acceptance/benchmark checks | All domain fixtures and acceptance criteria |
| FastAPI / asyncpg | defer | No V1 service boundary or concurrency need | Reconsider only from measurements/client demand |
| tree-sitter | defer | Code-aware parsing not needed for first Markdown corpus | Add only with language-specific evaluation cases |

Official references include [PostgreSQL full-text search](https://www.postgresql.org/docs/current/textsearch.html), [pgvector](https://github.com/pgvector/pgvector), [pgvector Python/SQLAlchemy integration](https://github.com/pgvector/pgvector-python#sqlalchemy), [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html), [Alembic](https://alembic.sqlalchemy.org/en/latest/), [psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), and [markdown-it-py](https://pypi.org/project/markdown-it-py/).

### Frameworks as references, not foundations

| Framework | Useful reference/benchmark | Why excluded from core |
|---|---|---|
| LlamaIndex | Node parsers, BM25/dense retriever comparison, ingestion-pipeline concepts | `VectorStoreIndex.from_documents()` and its document/node/storage model hide and own parsing, chunking, embeddings, and retrieval |
| Haystack | Strongest external PostgreSQL/hybrid benchmark; visible pipeline components and RRF alternatives | `DocumentStore`/retrievers still hide SQL schema, query, and ranking that AgentForge needs to teach |
| LangChain | Thin `BaseRetriever`/Embeddings interoperability and benchmark adapter | Convenience loaders/splitters/vector stores/chains add a large changing surface and obscure pipeline ownership |

Framework adapters, if built in Phase 9, consume AgentForge's frozen pre-chunked corpus and never become runtime dependencies or canonical types. Relevant official references: [LlamaIndex VectorStoreIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/), [Haystack pipelines](https://docs.haystack.deepset.ai/docs/creating-pipelines), [Haystack pgvector store](https://docs.haystack.deepset.ai/docs/pgvectordocumentstore), and [LangChain retrieval](https://docs.langchain.com/oss/python/langchain/retrieval).

## 27. Answers to the required design questions

| # | Question | Decision |
|---:|---|---|
| 1 | What exactly is stored in PostgreSQL? | Projects, logical documents, immutable document revisions, persisted derived chunks, memory identities/revisions/relations, evidence references, embedding-generation registry, separate derived chunk/memory vectors and FTS, and ingestion job state/config-policy fingerprints. Configured roots remain configuration rather than a V1 relational synchronization subsystem. Evaluation datasets/reports stay in version-controlled files. |
| 2 | What is a document? | A scoped logical source identity, independent of discovery path, whose immutable revisions store normalized full-text snapshots, hashes, normalizer identity, and source metadata. |
| 3 | What is a chunk? | A deterministic, rebuildable retrieval fragment of a document revision with structure and source locators. |
| 4 | What is a memory? | Deliberately recorded typed knowledge with immutable revisions, lifecycle state, scope, and evidence—not a copied vector chunk. |
| 5 | What is an embedding? | A model-versioned derived vector for one chunk or memory revision. |
| 6 | Which data is canonical? | Project identities, document identities/revisions, memory identities/revisions/relations, evidence links, and evaluation expectations. |
| 7 | Which data is derived/rebuildable? | Chunks, `tsvector`, embeddings, search indexes, excerpts, ranking explanations/caches, and evaluation run outputs. |
| 8 | How are project and global scopes represented? | `scope_kind` plus nullable `project_id`, protected by a check constraint; default predicate is current project OR global. |
| 9 | How does project discovery work? | Walk upward from cwd to the nearest `.agent-team/config.toml` containing a stable committed UUID; path/name never define identity. |
| 10 | How is lexical search implemented? | An exact/literal lane plus PostgreSQL FTS using explicit `simple` configuration, GIN, `ts_rank_cd`, scoped/status-filtered SQL, and deterministic ties. |
| 11 | How is semantic search implemented? | Query embedding from the active provider/model and exact pgvector cosine search first; measured partial HNSW later if justified. |
| 12 | How are results fused? | Each lane quota-collects both scopes, merges by common lane score, collapses chunks to canonical targets, assigns ranks, then applies explainable RRF (`k=60`) over exact/lexical/semantic and later planning lanes. |
| 13 | How is provenance preserved? | Canonical evidence references point to immutable document revisions and stable URI/locators; chunk IDs are optional accelerators, never sole evidence. |
| 14 | How is stale/superseded knowledge handled? | Current flags and explicit memory states/relations; excluded by default, retrievable in historical mode, never destructively replaced. |
| 15 | How does an agent write reusable knowledge? | Explicit structured `memory add/revise/validate/supersede` commands; strong claims require evidence; automatic extraction is deferred. |
| 16 | How does an agent retrieve old knowledge? | Diagnostic commands expose `memory search/related` and `context query/task`; the normal `agentctl` task-start/resume lifecycle automatically invokes planning retrieval and returns mandatory task data plus bounded historical context. |
| 17 | How is the vector index rebuilt? | Create/delete a selected derived embedding generation/index, re-embed canonical chunk/memory text by hashes, validate dimensions/completeness/evaluation, then atomically activate. |
| 18 | How is changed source content detected? | Raw-byte SHA-256 plus normalizer version/content hash controls canonical revisions; parser/chunker versions independently control derived rebuilds. |
| 19 | How is token usage reduced? | Compact hits first, selective canonical fragment fetch, deduplication, deterministic greedy selection, and explicit historical budget. |
| 20 | How is retrieval quality measured? | Versioned expected-source queries; recall/precision/MRR/rank, irrelevant hits, tokens, latency, anti-repeat, handoff, scale, and recovery. |
| 21 | How are repeated failures prevented? | Planning retrieval has explicit validated-failure/current-decision lanes and reserved context slots; normal task start/resume invokes it automatically; the benchmark must place the failure top three. |
| 22 | Which libraries are used and why? | Focused primitives in §26; each supplies generic parsing/storage/config/model access without owning RAG semantics. |
| 23 | Which RAG concepts remain explicit? | Source selection/hashing, parsing-to-domain mapping, chunking, embedding-generation registry, SQL candidates, filters, RRF, provenance, context selection, token budgets, and evaluation. |
| 24 | Which complexity is deferred? | Daemon/API, RBAC/tokens, cloud storage, UI, knowledge graph, auto-extraction, learned reranking, code AST parsing, remote sync, and distributed/multi-user operation. |

## 28. Cross-phase dependency and exit map

```text
Phase 0 disposable learning slice (no production-code dependency)

Phase 1 foundation
  -> Phase 2 documents/chunks
     -> Phase 3 embeddings/semantic
        -> Phase 4 usable document RAG
           +-> Phase 5 optional structured-memory corpus
           +-------------------------------+
                                             v
                                      Phase 6 context
                                        -> Phase 7 automatic task workflow
                                           -> Phase 8 Registar bootstrap
                                              -> Phase 9 final evaluation
```

Phase 0 transfers observations, not code or schema. No production phase proceeds merely because its code exists; tests and exit evidence must pass. Phase 4 is a complete document-only RAG milestone. Phase 5 adds an optional knowledge type, while Phase 6 must still build document-only context when memory is disabled. Phase 9 can send the project backward: poor chunking returns to Phase 2; embedding misses to Phase 3; lexical/fusion misses to Phase 4; provenance/lifecycle failures to Phase 5; token failures to Phase 6.

## 29. Assumptions and unresolved questions

### Assumptions made by this plan

- The developer accepts running one local PostgreSQL/pgvector instance.
- The existing `agentctl` can host additional subcommands without a breaking rewrite.
- Markdown/plain text contains enough high-value initial evidence to validate RAG before richer parsers.
- Project context isolation is sufficient because all agents run as the same OS user.
- Explicit memory writes are acceptable in V1.
- Thousands to low hundreds of thousands of items are the near-term scale; exact vector search is a valid starting baseline.

### Questions requiring owner or implementation-time resolution

1. Where is the current `agentctl` source, and what package/CLI/config contracts must be preserved?
2. Should AgentForge only connect to a user-managed PostgreSQL DSN, or may `agentctl system init/up/down` manage a pinned Docker Compose instance? Recommendation: support configured DSN first; add managed Compose only after core retrieval works.
3. Which local embedding model and license should be the reference configuration? Select through the Phase 0 observation and a small benchmark, not architecture hard-coding. Which non-local adapters, if any, merit later explicit egress approval?
4. What historical-context budget should agent integrations request by default? Start configurable; measure during Phase 9.
5. Where is the Registar repository, and which sources have authoritative precedence when documents conflict?
6. Should global-memory writes require an explicit `--scope global` confirmation in interactive human mode? Recommendation: yes for accident prevention, not security.
7. What canonical backup/restore user experience is desired? PostgreSQL `pg_dump`/`pg_restore` is sufficient technically; a thin `agentctl system backup/restore` wrapper may be added only after restore testing.

These questions do not justify guessing during implementation. Tasks that depend on them have explicit stop conditions.

## 30. Critical architecture self-review

This review was performed after drafting the architecture and task plan, then repeated against the external GPT review. The repair requests were not adopted mechanically: provider locality was relaxed without weakening egress safety; the learning spike was isolated from production; source membership was removed from V1 rather than merely postponed inside Phase 1; memory was made an optional corpus type; and automatic retrieval was attached to the normal task lifecycle.

### Unnecessary complexity

**Finding:** A daemon/API, RBAC/token hierarchy, async database stack, knowledge graph, automatic extraction, approximate vector index, and database-backed evaluation registry would all add moving parts without advancing the V1 learning goal.  
**Correction:** FastAPI, asyncpg, security roles/tokens, graph storage, auto-extraction, advanced reranking, and persisted source-set membership remain deferred. Exact vector search is the baseline. Evaluation definitions/results were removed from the production schema and remain version-controlled files. HNSW requires a measured decision task. Configured-root union scans cover the initial corpus without designing a general synchronization system first.

**Remaining justified complexity:** PostgreSQL is heavier than SQLite, but one installation supplies durable relational state, transactions, FTS, pgvector, filtering, migrations, and backup. That consolidation is simpler than operating separate document, vector, and search stores.

### Hidden RAG mechanics

**Finding:** SQLAlchemy, markdown parsers, and embedding clients can become accidental frameworks if their convenience layers decide retrieval behavior.  
**Correction:** AgentForge owns parsed-block mapping, chunk boundaries, hashes, embedding generations, SQL candidate queries, filters, RRF, deduplication, context selection, and metrics. Retrieval SQL lives in lane-specific modules and returns explanations. Libraries expose syntax, transport, and database primitives only.

### Framework/provider coupling

**Finding:** A canonical framework `Document`/`Node`, fixed embedding dimension, or remote provider schema would make replacement costly.  
**Correction:** Domain types are AgentForge-owned. Embedding model/dimension/config are registry data. Vectors are derived in two FK-safe tables and can coexist across models. Frameworks appear only as Phase 9 adapters. A small local model is the reference V1 learning path, not an architectural locality invariant; future adapters fit the same protocol and require explicit egress controls when they send text off-machine.

**Intentional coupling:** V1 is explicitly coupled to PostgreSQL and pgvector. Hiding that behind a generic database interface would reduce learning and create unused abstraction. Portability is supplied by canonical exports/rebuildability, not by pretending SQL backends are interchangeable.

### Documents, chunks, memories, embeddings, and indexes

**Finding:** The first draft allowed parser identity to blur canonical document revisions and used a polymorphic embedding target that weakened foreign keys.  
**Correction:** Document revisions store reparsable normalized source snapshots and raw hashes. Parser/chunker versions live with derived chunks. Chunk and memory embeddings use separate physical tables with real foreign keys. Chunks remain persisted but rebuildable. Evidence never relies on a chunk foreign key alone.

### Provenance and lifecycle

**Finding:** Rebuilding chunks could invalidate provenance if memories linked only to chunk IDs.  
**Correction:** Evidence references point to immutable document revisions plus stable URI/line/character locators and hashes. Memory updates append immutable revisions. Validation, rejection, supersession, and archive retain actor, time, and reason. Default search excludes stale states; historical mode exposes them.

### Project plus global retrieval

**Finding:** A single combined candidate query could allow a much larger global corpus to exhaust candidate limits before project results are considered, or vice versa.  
**Correction:** Each lane collects bounded project/global quotas, then merges candidates by the lane's common score before assigning one lane rank. Scope receives no extra RRF vote; project wins only exact-score ties. Other projects are absent unless a later explicit mode is designed.

### Rebuildability and failure isolation

**Finding:** The first draft activated a document only after embeddings, accidentally making canonical ingestion depend on a model/provider.  
**Correction:** Canonical document revision, chunks, and lexical projection activate transactionally; embeddings run independently and resumably. Provider failure degrades semantic retrieval visibly but does not lose or hide canonical/lexical knowledge. Phase 7 requires a destructive-derived-state rebuild acceptance test with canonical checksums.

### Preventing repeated rediscovery

**Finding:** General top-k search alone cannot guarantee that a prior failure survives ranking, and agents may skip search entirely.  
**Correction:** The planning profile adds validated-failure and current-decision lanes plus reserved context capacity. `agentctl context task` defaults to `planning`; free-form `context query` defaults to `default`. More importantly, the normal task-start/resume hook automatically invokes planning retrieval and returns it beside deterministic task context, so the ordinary workflow does not depend on remembering a separate search command. Phase 9 fails if differently worded proposals do not place the known failure in the top three.

**Residual limitation:** V1 does not autonomously block a repeated approach. An agent can still bypass `agentctl`, and an irrelevant retrieved warning may be ignored. Hard enforcement is deferred because it adds workflow coupling and false-positive risk.

### Learning sequence and memory optionality

**Finding:** The production-first sequence delayed visible semantic retrieval until after packaging, configuration, discovery, migrations, and several domain tables. It could teach infrastructure before teaching RAG, and the linear phase diagram made structured memory look necessary for retrieval.  
**Correction:** Phase 0 is a deliberately disposable one-document semantic vertical slice with no production interfaces. Phase 4 is now an explicit usable document-only RAG milestone. Memory tables are not created in Phase 1; Phase 5 optionally adds structured memory as another retrieval corpus type, and Phase 6 must pass with memory disabled.

### Phase order, fusion unit, and execution contracts

**Finding:** An independent review found that the first task order asked Phase 4 to implement failure/decision planning before Phase 5 defined memory semantics; it also left chunk-to-document aggregation timing ambiguous and called tasks delegable without a complete worker authority contract.  
**Correction:** Phase 4 now ends with generic exact/lexical/semantic fusion. Phase 5 adds lifecycle-aware planning lanes after invariants exist. Every lane collapses chunks to one canonical document target before assigning lane ranks, retaining up to three passages and preventing multi-hit boosts. §15 now supplies the mandatory source precedence, assumptions, exclusions, authority, evidence, output, acceptance, and stop conditions for every delegated task.

### Ingestion ownership and synchronous boundary

**Finding:** A partial path ingestion could have deactivated files it never scanned; the attempted fix introduced source-set and many-to-many membership machinery before a real corpus demonstrated that need. Normalizer changes were also undefined, and async/NumPy protocols contradicted the chosen synchronous optional-dependency architecture.  
**Correction:** V1 canonicalizes and deduplicates the union of configured roots. Only a successful full scan of that entire `(scope, project)` corpus may infer absence; partial paths and interrupted runs are additive. Independent root ownership/membership is deferred. Normalizer changes create canonical revisions; parser/chunker changes rebuild derived rows. Core protocols are synchronous and return provider-neutral nested sequences.

### Security proportionality

**Finding:** The obsolete architecture treated projects as hostile tenants even though every agent already runs as the same OS user.  
**Correction:** V1 uses one OS owner, one database credential, logical scope filters, and safe defaults. There are no project users, tokens, RBAC, admin hierarchy, or security gateway. Secrets are protected only at normal machine-configuration boundaries.

### Review result

The architecture is proportionate for V1 after the corrections above. Its main unresolved risks are not hidden: current `agentctl` compatibility and task-start hook, local PostgreSQL installation experience, reference embedding model/provider and any future egress policy, Registar source precedence, and empirical retrieval quality. Each has an explicit decision or stop point before dependent implementation.

## 31. Alternatives retained for later review

- **Generated versus explicitly maintained `tsvector`:** use stored generated columns while one fixed `simple` configuration suffices. Switch to explicit per-configuration derived rows only if multilingual needs appear.
- **Dimensionless vectors versus table per model/dimension:** use dimensionless vectors in separate chunk/memory embedding tables for flexible side-by-side generations; add model-specific partial expression indexes only after benchmarks. A table per fixed dimension is safer but creates schema churn for experiments.
- **RRF versus weighted fusion:** RRF is the default because ranks are comparable while raw lexical/vector scores are not. Weighted normalized fusion remains an evaluation variant.
- **Direct CLI versus service:** direct execution is V1. A local service becomes reasonable only for warm model ownership, background work, or multiple non-CLI clients demonstrated by measurement.
- **Explicit memory versus automatic extraction:** explicit writes are V1. Later extraction may produce proposed candidates for review, never silently validated truth.
- **Configured-root union versus source membership:** V1 scans and deduplicates one configured root union per corpus. Add persisted source-set memberships only if real independent root lifecycles make union reconciliation insufficient.
- **PostgreSQL versus embedded database:** PostgreSQL is selected for one coherent teaching/production path; an embedded backend may be reconsidered only if installation friction prevents adoption.

## 32. Approval and stop condition

This document is the complete proposed architecture and implementation sequence, not authorization to execute it. External review should challenge the data model, direct-CLI decision, chunking defaults, provider boundary, retrieval profiles, evaluation thresholds, and unresolved questions.

After review, revise this document until the owner explicitly approves it. Only then may implementation planning be converted into tracked execution tasks. No Phase 1 scaffolding, dependency installation, database creation, or product code begins from this document alone.

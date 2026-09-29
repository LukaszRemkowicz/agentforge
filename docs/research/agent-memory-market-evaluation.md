# AgentForge Agent-Memory Market Evaluation

**Research date:** 2026-09-29  
**Decision scope:** Task 0 only; no production implementation  
**Evidence policy:** current official documentation, official repositories, official release/license files, and one reproducible local API spike  
**Status:** provisional market screen and spike plan; Task 0 is not complete until the mandatory finalist service spikes run

## Executive decision

The documentation evidence supports a **provisional WRAP direction**, not a completed backend selection. AgentForge should not adopt a memory product as its trust boundary and should not build a complete memory engine before the mandatory spikes decide whether a wrapper is viable.

The recommended shape is:

```text
Codex / Claude / future agents
             |
             v
          agentctl
             |
             v
AgentForge local control plane
  - project/admin authentication
  - authorization and global-promotion policy
  - canonical engineering-memory envelope
  - provenance and lifecycle rules
  - query planning and token budgets
  - audit/export/backup orchestration
  - canonical memory_records + memory_revisions tables
             |
             v
Hindsight adapter (preferred retrieval engine, spike-gated)
             |
             v
Hindsight-derived retrieval projection
             |
             v
local PostgreSQL + pgvector
```

**Preferred candidate for the finalist spike:** [Hindsight](https://github.com/vectorize-io/hindsight). It is the closest fit discovered on paper: local/self-hosted deployment, PostgreSQL, semantic + keyword + graph + temporal retrieval, memory banks, token-bounded recall, export/import, audit/validation extension points, and direct coding-agent integrations. It is also pre-1.0 and its project-token and canonical-record round-trip guarantees are not proven by documentation, so it must pass the common acceptance harness before it can be selected.

**Fallback:** [Mem0 OSS](https://github.com/mem0ai/mem0) behind the same AgentForge boundary. Mem0 is more established as a general memory engine and has a strong current self-hosted server, but AgentForge would own more temporal/supersession behavior; Mem0's richer graph and temporal layer is currently a managed-platform feature.

**Do not combine engines in Phase 0.** Running Hindsight plus Graphiti or Mem0 would duplicate extraction, indexes, persistence, and truth reconciliation before benchmarks justify that complexity. Graphiti is the best later component if the selected engine cannot meet temporal/provenance tests.

This provisional direction does **not** authorize implementation and is not Task 0 completion. The mandatory service-level security, memory-quality, provenance, temporal, offline, and token-efficiency spikes in this report are go/no-go gates.

## 1. AgentForge requirements

### Non-negotiable product boundary

- One machine-level memory service, not one service per managed repository.
- Stable project identity independent of path or repository name.
- Default retrieval is `current project + global`; other projects are denied.
- Project credentials and the human administrator credential are distinct.
- Authorization is enforced outside the project-scoped agent process.
- Existing Codex and Claude harnesses remain; a backend may not require its own agent runtime.
- Important memory remains in a durable canonical store. An index is never the sole copy.
- Mandatory operating rules remain deterministic context, not semantic-only retrieval.

### Canonical engineering-memory needs

- Types such as observation, hypothesis, finding, failure, solution, decision, and summary.
- Lifecycle states such as draft, proposed, validated, rejected, superseded, and archived.
- Source provenance to project/task/experiment/run/report/file/document/commit/agent/time/external source.
- Explicit current-vs-historical behavior; superseded material is excluded by default but inspectable.
- Exact identifiers and code tokens as well as semantic paraphrases.
- Concise ranked results first, followed by selective source-fragment fetches.
- A proposal/review path for project knowledge promoted into global memory.

### Trust model

The backend's namespace field is not a security boundary unless the service binds it to authenticated credentials. A project agent must never be able to choose another project's namespace. “The client always sends the right filter” is a failing design.

## 2. Method and limitations

The mandatory candidates were researched independently against official sources: Mem0; Letta/Letta Code/MemFS; Graphiti; Zep; and LangGraph Store. Candidate discovery added Hindsight, Cognee, and Supermemory. PostgreSQL + pgvector + PostgreSQL full-text search is the custom baseline.

The evaluation distinguishes:

- `N` — native/documented;
- `P` — partial or native with an important limitation;
- `W` — AgentForge wrapper/policy/schema required;
- `C` — convention only, not an authorization boundary;
- `X` — absent or not documented;
- `U` — unclear; must be proven.

Documentation can establish capability and architectural fit, but it cannot prove adversarial isolation, retrieval quality on AgentForge data, or operational recovery. A reproducible LangGraph primitive spike was executed; full service spikes were not faked. Docker became available during research, but Hindsight/Graphiti/Mem0 quality tests require provider/model setup and persisted test instances. Those tests are specified below as pre-implementation gates.

### Evidence snapshot

| Candidate | Assessed release/version | Reproducibility note |
|---|---|---|
| Hindsight | v0.10.1, 2026-09-21 | Release identified; official `main` docs accessed 2026-09-29. Pin tag/commit for spike. |
| Mem0 | v2.2.1, 2026-09-25 | Package/release identified; pin `mem0ai==2.2.1` and matching server image/commit. |
| LangGraph | 1.2.12 | Exact package executed locally; dependency versions recorded in §8. |
| Letta Code | 0.33.2 | Package metadata assessed; pin exact server/runtime commit before any spike. |
| Cognee | v1.6.1, 2026-09-24 | Screening only. |
| Graphiti | official `main` docs accessed 2026-09-29 | Exact release/commit was not recorded; this is an evidence gap to close before a service spike. |
| Zep | managed documentation/pricing accessed 2026-09-29 | Cloud service has no customer-pinnable server release in this evaluation. |
| Supermemory | official repository/docs accessed 2026-09-29 | Screening only; exact server release and license entitlement must be pinned. |

## 3. Candidate disposition

| Candidate | Category | Disposition | Main reason |
|---|---|---|---|
| Hindsight | **WRAP** | Preferred finalist, not selected | Best paper fit to temporal/graph/keyword memory, banks, token budgets, export, and coding-agent integration; pre-1.0 and ACL/canonical-round-trip behavior need proof. |
| Mem0 OSS | **WRAP** | Fallback | Mature memory CRUD/extraction/retrieval/history and self-hosted API; engineering lifecycle, provenance policy, and project ACL remain AgentForge-owned. |
| Graphiti | **COMPONENT / WRAP** | Temporal specialist | Excellent temporal KG, source episodes, hybrid search, and supersession; no native multi-credential authorization and higher graph/LLM operational cost. |
| LangGraph Store | **COMPONENT** | Viable low-level substrate | Clean independent Store API and namespaces; no memory epistemology, history, auth, service, or hybrid lexical retrieval. |
| Letta APIs/App Server | **WRAP** | Secondary | Strong stateful memory, archives, blocks, and MemFS; semantics/security still need a wrapper. |
| Letta Code runtime | **REJECT** | Boundary conflict | It is an agent/coding harness and would replace or duplicate the existing Codex/Claude workflow. |
| Cognee | **REJECT for Task 0** | Screened watch list | Rich graph/RAG pipeline and local deployment, but documentation gaps in auth, history, token budgeting, backup/export, and temporal semantics prevent a decision-grade 57-point evaluation. |
| Supermemory | **REJECT for Task 0** | Screened watch list | Attractive local single-binary design, but licensing/document cap, scoped credentials, history/export, provenance, and stability remain too unclear for finalist status. |
| Zep | **REJECT for local-first** | Managed option only | Strong managed service, but Community Edition is deprecated; local-first use conflicts with cloud/BYOC and paid governance. |
| Custom PostgreSQL stack | **CUSTOM** | Fallback/control benchmark | Exact policy and ownership, but highest extraction, ranking, lifecycle, API, and maintenance burden. |

## 4. Candidate summaries

### 4.1 Hindsight

Hindsight is the strongest additional candidate. It exposes `retain`, `recall`, and `reflect`; combines semantic, keyword, graph, and temporal retrieval; organizes memory into banks; supports token-bounded recall; and publishes Codex/Claude/MCP integrations. It can run locally in Docker or bare metal with embedded PostgreSQL for development and external PostgreSQL for production. Local embeddings/reranking are available; an LLM is still needed for extraction and consolidation.

Its extension system documents API-key/tenant auth, validation hooks, and audit hooks, while export/import supports instance portability. Those are promising primitives, not proof that a project credential is cryptographically limited to `project A + global`. AgentForge should place its own gateway in front regardless.

Primary risks are the pre-1.0 release line, extraction misclassification, authorization extension complexity, PostgreSQL/model footprint, and rapid schema/API change. Pin an exact release and treat the canonical AgentForge envelope as portable data.

Official evidence: [repository and MIT license](https://github.com/vectorize-io/hindsight), [API](https://github.com/vectorize-io/hindsight/blob/main/hindsight-api/README.md), [installation and local deployment](https://github.com/vectorize-io/hindsight/blob/main/skills/hindsight-docs/references/developer/installation.md), [extensions](https://github.com/vectorize-io/hindsight/blob/main/skills/hindsight-docs/references/developer/extensions.md), [Codex integration](https://github.com/vectorize-io/hindsight/blob/main/hindsight-integrations/codex/README.md), [releases](https://github.com/vectorize-io/hindsight/releases).

### 4.2 Mem0

Mem0 OSS provides memory add/get/search/update/delete/history, LLM extraction, metadata filters, pluggable LLMs/embedders/vector stores, rerankers, and a Docker self-hosted server. The current server includes admin setup, per-user API keys, authentication enabled by default, request audit logs, Postgres + pgvector, and migrations.

It fits cleanly behind AgentForge and does not replace the agent runtime. Its entity scopes (`user_id`, `agent_id`, `app_id`, `run_id`) are query identifiers; official docs do not establish project-level ACLs that implement the required token matrix. Current OSS extraction is ADD-only, which preserves old material but leaves current/superseded semantics to AgentForge. Managed graph/temporal features are not equivalent to the OSS engine.

Official evidence: [OSS overview](https://github.com/mem0ai/mem0/blob/main/docs/open-source/overview.mdx), [configuration](https://github.com/mem0ai/mem0/blob/main/docs/open-source/configuration.mdx), [self-hosted setup](https://github.com/mem0ai/mem0/blob/main/docs/open-source/setup.mdx), [search](https://github.com/mem0ai/mem0/blob/main/docs/core-concepts/memory-operations/search.mdx), [v2-to-v3 migration](https://github.com/mem0ai/mem0/blob/main/docs/migration/oss-v2-to-v3.mdx), [Apache-2.0 license](https://github.com/mem0ai/mem0/blob/main/LICENSE).

### 4.3 Graphiti

Graphiti is an open-source temporal knowledge-graph engine. It stores raw episodes, entities, and fact edges with validity windows; new episodes can invalidate older facts without deleting historical evidence. Retrieval combines semantic/vector, BM25, graph traversal, and multiple rerankers. `group_id` supports logical graph partitioning and multi-group queries. Local deployments support FalkorDB/Neo4j and local/OpenAI-compatible model providers; an experimental MCP/HTTP server is included.

This is the best provenance/temporal component in the mandatory set, but official namespacing guidance explicitly leaves authorization to the application. It lacks project credentials, admin roles, global-write policy, and a request audit boundary. Use it only behind AgentForge; do not expose its caller-selected `group_id` directly.

Official evidence: [README](https://github.com/getzep/graphiti/blob/main/README.md), [episodes](https://help.getzep.com/v2/graphiti/core-concepts/adding-episodes), [CRUD](https://help.getzep.com/graphiti/working-with-data/crud-operations), [namespacing](https://help.getzep.com/graphiti/core-concepts/graph-namespacing), [search](https://help.getzep.com/graphiti/working-with-data/searching), [MCP server](https://github.com/getzep/graphiti/blob/main/mcp_server/README.md), [Apache-2.0 license](https://github.com/getzep/graphiti/blob/main/LICENSE).

### 4.4 Zep

Zep Cloud provides users/sessions/groups, temporal facts, episode provenance, vector + BM25 + graph retrieval, rerankers, bounded context assembly, API keys, logs, and enterprise governance. It is not the current local-first continuation of old Zep Community Edition: Community Edition is deprecated, ordinary deployment is managed cloud, and BYOC plus ABAC/RBAC/audit controls are enterprise features.

Zep is technically capable but conflicts with the “one local system per developer machine” goal and introduces a service/price dependency at the security boundary. Reconsider only if the product boundary changes to permit managed cloud.

Official evidence: [concepts](https://help.getzep.com/v2/concepts), [facts](https://help.getzep.com/facts), [search](https://help.getzep.com/searching-the-graph), [ABAC](https://help.getzep.com/attribute-based-access-control), [governance](https://help.getzep.com/v3/governance), [FAQ/self-hosting](https://help.getzep.com/faq), [pricing](https://www.getzep.com/pricing/).

### 4.5 Letta, Letta Code, and MemFS

Letta's APIs and App Server can be called by external agents, so the memory layer can be wrapped without adopting Letta Code. Memory blocks, archives/passages, message history, and git-backed per-agent MemFS provide useful durable state and human inspection. Local/self-hosted deployment, REST/SDKs, MCP, PostgreSQL/pgvector, and local model endpoints are documented.

Letta Code itself includes the harness, terminal UI, App Server, channels, and runtime. Adopting it would cross AgentForge's product boundary. MemFS also defaults to per-agent repositories, while AgentForge needs project-shared memory and server-enforced project/global policy. Shared archives/blocks can help, but the AgentForge gateway still owns authorization and lifecycle. Concurrent full memory-block replacement is last-write-wins and must be tested.

Official evidence: [Letta repository](https://github.com/letta-ai/letta), [Letta Code](https://github.com/letta-ai/letta-code), [App Server](https://docs.letta.com/self-hosting/app-server), [MemFS](https://docs.letta.com/concepts/memfs), [memory](https://docs.letta.com/configuration/memory), [archives API](https://docs.letta.com/api/resources/archives), [PostgreSQL](https://docs.letta.com/guides/docker/postgres).

### 4.6 LangGraph Store

LangGraph `BaseStore` is an independent storage abstraction with tuple namespaces and `put/get/delete/search/list_namespaces`. Official docs instantiate it outside a graph. Persistent adapters include PostgreSQL and other stores; semantic search and metadata filtering are built in.

It is a useful component, not a complete memory backend. It lacks history, supersession, epistemic types, lexical/hybrid retrieval, credentials, authorization, audit, and a standalone service. AgentForge would build almost all policy and service behavior. Namespace-prefix security advisories make exact segment-boundary tests mandatory.

Official evidence: [Store docs/source](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/stores.mdx), [long-term memory](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/add-memory.mdx), [package](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/pyproject.toml), [security advisories](https://github.com/langchain-ai/langgraph/security/advisories).

### 4.7 Cognee and Supermemory

Cognee is a credible local graph/RAG pipeline with Python, REST, MCP, local models, datasets, hybrid retrieval, and recent provenance work. Its flexible backends and pipeline increase operational surface; local auth is normally disabled until configured, so permission and dataset isolation need adversarial testing. See [repository](https://github.com/topoteretes/cognee), [API](https://docs.cognee.ai/api-reference/introduction), [MCP](https://github.com/topoteretes/cognee/blob/main/cognee-mcp/README.md), and [license](https://github.com/topoteretes/cognee/blob/main/LICENSE).

Supermemory advertises a local single-binary server with embedded graph, local embeddings, provider flexibility, containers/metadata, search, and contradiction handling. Its self-hosted “lite” document cap, per-project credential semantics, export/audit behavior, and fast-moving product boundary require proof. See [repository](https://github.com/supermemoryai/supermemory), [self-hosting](https://github.com/supermemoryai/supermemory/blob/main/apps/docs/self-hosting/quickstart.mdx), and [filtering](https://docs.supermemory.ai/memory-api/features/filtering).

### 4.8 Custom PostgreSQL baseline

A custom AgentForge service on PostgreSQL, pgvector, PostgreSQL full-text search, and local embeddings can exactly implement the trust and lifecycle model. PostgreSQL row-level security is a strong server-side substrate; pgvector provides exact/approximate vector search; PostgreSQL provides full-text search, transactions, backup, PITR, and mature operations.

The cost is that AgentForge would own extraction, deduplication, hybrid score fusion, reranking, embedding orchestration, history/supersession schema, APIs, auth, audit, migrations, evaluations, and observability. It is the control benchmark and fallback, not the first choice while viable wrapped engines exist.

Official evidence: [PostgreSQL full-text search](https://www.postgresql.org/docs/current/textsearch-controls.html), [row-level security policies](https://www.postgresql.org/docs/current/sql-createpolicy.html), [backup](https://www.postgresql.org/docs/current/backup.html), [pgvector](https://github.com/pgvector/pgvector).

## 5. Required comparison matrix

The matrix answers all 57 required questions for the preferred discovered candidate, every mandatory candidate, and the custom baseline. A status describes the fit to AgentForge, not whether the vendor has a similarly named feature. `W` is often the correct result because AgentForge deliberately owns its trust and epistemic policy.

### Deployment (1–6)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Fully local | N | N | N | X | N | N | N |
| 2 | Docker | N | N | N | X | N | U | N |
| 3 | No required cloud dependency | N | N | N | X | N | N | N |
| 4 | Local embeddings | N | N | N | X/U | N | N | N |
| 5 | Configurable/local LLM | N | N | N | X | N | N | N |
| 6 | Required databases/services understood | P: PostgreSQL/vector | N: Qdrant/SQLite or PG | N: graph DB | N: managed | N: files or PG | N: selected adapter | N: PG/pgvector |

### Memory operations (7–14)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 7 | Add | N | N | N | N | N | N | W |
| 8 | Exact read | N | N | N | N | N | N | W |
| 9 | Semantic search | N | N | N | N | N | N | W |
| 10 | Update | U/P | N | N | P | N | N: overwrite | W |
| 11 | Archive/delete | P | P: delete/expiry | P | N | N | N: delete | W |
| 12 | History | P | N | N | N | N | X | W |
| 13 | Supersession | P/W | W | N | N | W | X | W |
| 14 | Related-memory retrieval | N | N | N | N | N | N | W |

### Retrieval (15–20)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 15 | Vector | N | N | N | N | N | N | N |
| 16 | Lexical/full-text | N | P | N | N | N | X | N |
| 17 | Hybrid | N | P | N | N | P | X | W |
| 18 | Metadata filters | P | N | N | N | P/U | N | N |
| 19 | Reranking | N | P | N | N | U | X | W |
| 20 | Context budgeting | N | W | W | N | P | W | W |

### Knowledge quality (21–26)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 21 | Memory types | N | P | N | N | N | W | W |
| 22 | Facts vs hypotheses | W | W | W | W | W | X | W |
| 23 | Provenance | N/P | W | N | N | P | W | W |
| 24 | Confidence/status | W | P/W | U | N | W | X | W |
| 25 | Superseded exclusion | P/W | W | P | P | W | X | W |
| 26 | Contradictions retained | P | P | P | N | P | N: unmodelled | W |

### Project model (27–31)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 27 | Namespaces | N: banks | P: entity scopes | N: groups | N | N | N: tuples | W |
| 28 | Multiple projects, one instance | N | N | N | N | N | N | W |
| 29 | Project-scoped query | N | N | N | N | P/W | N | W |
| 30 | `project + global` retrieval | W | W | N: multi-group | P | N/P | N: compose calls | W |
| 31 | Cross-project denied by default | W/U | W | C/W | N | W | W | W: gateway/RLS |

### Security (32–38)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 32 | Multiple credentials | P | N | X | N | N | X | W |
| 33 | Scoped credentials | P/U | U | X | P/N | U | X | W |
| 34 | Server-side authorization | P: extension | P: auth, project ACL U | X | N | N/P | X | W |
| 35 | Project token reads project + global only | W/U | W | X | P | W | W | W |
| 36 | Global writes separately protected | W | W | X | P | W | W | W |
| 37 | Admin role | U/P | P | X | N/P | N/P | W | W |
| 38 | Audit log | P: hook, off by default | N | X | P: plan dependent | U | W | W |

### Agent integration (39–45)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 39 | Existing Codex/Claude; no runtime replacement | N | N | N | N | N for APIs; X for Code runtime | N | N |
| 40 | Python client | N | N | N | N | N | N | W |
| 41 | CLI | N | N | W | N | N | X | W |
| 42 | MCP | N | N | N | N | N | X | W |
| 43 | HTTP API | N | N | N | N | N | X | W |
| 44 | Local daemon/IPC | N | X: HTTP stack | N | X | N | X | W |
| 45 | Clean AgentForge wrapper | N | N | N | N | N | N | W |

### Operations (46–52)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 46 | Backup/restore | N/P | W: DB tools | P: volumes | U/X | N/P | W: adapter | N |
| 47 | Migrations | N | N | U | U | N | N for PG setup | W |
| 48 | Reindex | U/P | W | N | U/X | U | W | P |
| 49 | Export/import | N | P | U/P | P | N/P | W | P |
| 50 | Offline recovery | N | W | P | X | N | W | N |
| 51 | Observability | N/P | P | P | P/N | N/P | W | W |
| 52 | Version stability | P: pre-1.0 | P: fast change | P | P | U/P | N: 1.x LTS | N/P |

### Licensing and ownership (53–57)

| # | Question | Hindsight | Mem0 | Graphiti | Zep | Letta APIs | LangGraph Store | Custom PG |
|---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 53 | License | N: MIT | N: Apache-2.0 | N: Apache-2.0 | P: service terms/OSS SDKs | N: Apache-2.0 | N: MIT | N: permissive |
| 54 | No cloud lock-in | N | N for OSS | N | X | N for self-host | N | N |
| 55 | No paid-only critical feature | N/P | P: graph/temporal managed | N | X/P | P: team features | U/N | N |
| 56 | Data portability | N | P | P/U | P | N/P | N | N |
| 57 | Long-term suitability | P/W | P/W | P | X for local-first | P/W | W | P: maintenance cost |

### Additional-candidate matrix summary

These candidates were screened and retained in the evidence record, but were **not promoted to serious/full-matrix candidates** because official documentation left too many of the 57 questions unresolved. They do not displace the Hindsight/Mem0 finalist pair.

| Area | Cognee | Supermemory |
|---|---|---|
| Deployment (1–6) | Local, Docker, local models: `N`; database/dependency surface: `P` | Local single binary/Docker, local models: `N`; embedded services: `N/P` |
| Memory operations (7–14) | Add/read/search/delete/related: `N`; update/history/supersession: `U/P` | Add/read/search: `N`; update/delete: `U/P`; history/supersession: `U` |
| Retrieval (15–20) | Vector/lexical/hybrid/filters: `N`; reranking and token budget: `U` | Vector and filters: `N`; lexical/hybrid/reranking/token budget: `U` |
| Quality (21–26) | Graph types/provenance: `P/N`; hypotheses/confidence/current-vs-superseded: `W/U` | Graph/profiles: `P`; provenance/status/contradiction claims: `U` until reproduced |
| Project model (27–31) | Datasets support scopes: `N/P`; default-deny and global composition: `U/W` | Containers/spaces: `N`; project credentials/default-deny/global composition: `W/U` |
| Security (32–38) | Auth/permissions exist but local auth may default off: `P`; exact project-token/admin/audit behavior: `U` | Bearer auth: `N`; scoped credentials/admin/audit: `U/W` |
| Integration (39–45) | Python/REST/MCP: `N`; CLI/daemon details: `P/U`; clean wrapper: `N` | API/SDK/MCP/local server: `N`; clean wrapper: `N` |
| Operations (46–52) | Backup/export/history/reindex partly unclear: `U/P`; active v1.6.1 | Backup/migration/reindex/export/audit mostly `U`; fast-moving |
| License (53–57) | Apache-2.0, portable core: `N`; long-term fit `W` pending spike | Repository MIT, but self-hosted Lite cap reported in official releases: `P`; suitability `W` |

## 6. Security findings

No local candidate should be trusted as AgentForge's authorization boundary without a gateway test.

| Candidate | Isolation classification | Finding |
|---|---|---|
| Hindsight | **wrapper-enforced / unproven native extension** | Banks provide namespaces; tenant/auth extensions are promising. The exact A/B/global/admin matrix is not documented as a default guarantee. |
| Mem0 | **wrapper-enforced** | Authentication, keys, and request logs are native. Entity IDs/scopes are filters; project-bound permissions are not established. |
| Graphiti | **client-convention-only without wrapper** | Official guidance places authorization of `group_id` on the application. |
| Zep | **native at cloud project level; paid/partial within project** | Project-bound keys exist; finer ABAC/user-group governance is enterprise and shared graphs may be project-wide. |
| Letta | **wrapper-enforced** | Local capability token protects the server, but independent project-token ACL behavior is not established. |
| LangGraph Store | **client-convention-only without wrapper** | A caller holding the Store can select any tuple namespace. |
| Custom PostgreSQL | **native only after AgentForge implements it** | Gateway authorization plus PostgreSQL RLS can enforce default deny; neither comes for free. |

The required gateway rule is:

```text
credential -> immutable principal and allowed scopes
request    -> operation, requested project/global scope
gateway    -> rejects unauthorized scope before backend query construction
backend    -> receives only trusted namespace/bank/filter values
```

Relying solely on backend metadata filters is prohibited. For defense in depth, a custom PostgreSQL layer should also use row-level security, with a non-bypass application role and transaction-local trusted principal context.

### Mandatory executable security harness

For each finalist, create `project A`, `project B`, `global`, `TOKEN_A`, `TOKEN_B`, and `ADMIN_TOKEN`; call the backend through AgentForge and then directly where possible.

| Operation | TOKEN_A | TOKEN_B | ADMIN |
|---|:---:|:---:|:---:|
| Read/write A | allow | deny | allow |
| Read/write B | deny | allow | allow |
| Read global | allow | allow | allow |
| Write global | deny; proposal only | deny; proposal only | allow |
| Choose/forge another scope | deny before backend call | deny before backend call | allow |
| Manage/revoke credentials | deny | deny | allow |

Also test encoded identifiers, prefix collisions (`A` versus `A-evil`), empty/missing scope, repeated query parameters, bulk endpoints, export, delete/clear, MCP tools, admin endpoints, and direct backend access. Any path that bypasses the gateway is a blocker.

## 7. Memory-quality, provenance, and temporal findings

### Native strength by candidate

- **Graphiti** has the clearest native model for source episodes, fact edges, validity windows, invalidation, and historical inspection.
- **Hindsight** has the broadest ready-made memory/retrieval mix for AgentForge, including temporal and graph retrieval, but AgentForge-specific epistemic states still require a canonical envelope.
- **Zep** is strong on managed temporal facts and context assembly, but fails the local-first boundary.
- **Mem0 OSS** preserves history and old/new material, but AgentForge must label contradictions and select current records.
- **Letta** offers durable blocks/archives/MemFS and useful Git history, not an engineering decision lifecycle.
- **LangGraph Store** stores arbitrary structured values; all meaning is application-owned.

### Canonical envelope AgentForge must own

Regardless of backend, every durable memory should carry fields equivalent to:

```text
memory_id
scope: global | project:<uuid>
type: note | observation | hypothesis | finding | failure | solution | decision | summary
state: draft | observed | proposed | validated | rejected | superseded | archived
title
body
source_refs[]
confidence?                 # explicit source or reviewer confidence, never invented silently
valid_from?
valid_until?
supersedes[]
contradicts[]
created_at / created_by
reviewed_at? / reviewed_by?
backend_refs[]              # backend IDs/index versions, not canonical identity
schema_version
```

The AgentForge control plane owns canonical `memory_records` and append-only `memory_revisions` tables in PostgreSQL. A backend may derive entities, embeddings, summaries, or graph edges into its own projection, but it may not silently overwrite canonical state. Extraction results begin as proposed/draft unless a deterministic workflow or authorized reviewer promotes them. A finalist may collapse canonical and backend storage into one physical PostgreSQL instance only if the spike proves lossless round-trip of every canonical field, immutable history, and rebuildability of all derived indexes; otherwise separate AgentForge tables remain authoritative.

### Mandatory executable quality corpus

Use exactly these core records plus distractors containing realistic error messages, symbols, filenames, commits, and reports:

```text
A / validated failure: Brightness-ranked sparse subsets failed under condition X.
A / hypothesis: Long-range neighbour descriptors may avoid the issue.
A / superseded decision: Astrometry.net is mandatory.
A / current decision: Astrometry.net is optional.
B / private finding: a semantically similar but confidential finding.
global / validated rule: Before repeating a failed experiment, retrieve prior failure evidence.
```

Acceptance checks:

1. Default A search returns A + global and never B.
2. Current decision ranks before/excludes superseded decision by default.
3. Historical mode returns the superseded decision and its evidence.
4. Hypothesis remains labelled; retrieval does not turn it into fact.
5. Semantic paraphrases retrieve the validated failure.
6. Exact IDs, symbols, filenames, and error strings are searchable.
7. Every result can reach the original source fragment.
8. `old decision -> new`, `hypothesis -> rejected`, `finding -> validated`, and `solution -> superseded` preserve a complete audit/history chain.
9. A contradictory new source is retained and flagged rather than silently erasing evidence.
10. Concurrent writes do not lose a validated record or create an unreviewed current decision.

## 8. Executed local spike: LangGraph Store 1.2.12

A temporary Python 3.12 environment used `langgraph==1.2.12`, `langgraph-checkpoint==4.2.0`, `langgraph-checkpoint-postgres==3.1.2`, and `langchain-core==1.6.6`. The spike used `InMemoryStore` with a deterministic test embedder so no external provider could influence the result.

Observed:

- tuple namespaces, exact `get`, semantic `search`, metadata filtering, structured values, and timestamps worked;
- filtering `status=validated` returned the current Astrometry decision while the superseded record remained exactly readable;
- a paraphrased failure query ranked the expected failure first;
- project and global queries had to be composed by the caller;
- a caller with raw Store access could read project B and could search the broad `("project",)` prefix, proving namespaces are not authorization;
- Store overwrite/history semantics do not provide AgentForge's lifecycle; distinct immutable records were needed;
- with 30 synthetic records, two top-1 searches returned two relevant chunks and zero irrelevant chunks: approximately 16 retrieved words versus 179 words for loading the whole synthetic corpus, in about 0.8 ms in-process.

The token result is a smoke test, not a backend benchmark: the corpus and embedder were synthetic, no persistent database was involved, and the timing excludes model/network cost. It proves the proposed measurement harness and confirms the security/semantics gap.

Reproduction artifact: `docs/research/spikes/langgraph_store_spike.py`.

## 9. Runtime compatibility

| Candidate | Can remain behind `agentctl`? | Runtime cost |
|---|---|---|
| Hindsight | Yes: REST/SDK/MCP | None beyond adapter/service process. |
| Mem0 | Yes: library or HTTP | None beyond adapter/service process. |
| Graphiti | Yes: Python/MCP/HTTP | Graph DB, extraction/model calls, and wrapper. |
| Zep | Yes: SDK/HTTP/MCP | Managed service/network dependency. |
| Letta APIs/App Server | Yes | Additional stateful agent server; avoid Letta Code runtime. |
| LangGraph Store | Yes: direct library | AgentForge must build the service boundary. |
| Custom PostgreSQL | Yes | AgentForge builds everything above the database. |

No finalist requires replacing Codex or Claude. Letta Code is rejected specifically because adopting its runtime would cross that boundary.

## 10. Token-efficiency evaluation

The production benchmark must compare identical tasks under:

```text
baseline: mandatory deterministic context + full manually selected history
candidate: mandatory deterministic context + metadata/result list + fetched source fragments
```

Record corpus size, indexed documents, query, top-k, retrieved chunks, approximate input tokens, relevant/irrelevant results, recall of required evidence, p50/p95 latency, extraction calls, reranker calls, and cost. Run exact-identifier, semantic-paraphrase, failure-recall, current-decision, and mixed project/global query classes.

Acceptance should be set by relevance first, tokens second. A candidate fails if it saves tokens by omitting a known failure or returning an unlabelled superseded decision. Hindsight's documented token budget and Zep's bounded context are useful; every other candidate can be budgeted by AgentForge after ranking.

## 11. Operations, deployment, and licensing findings

- Prefer a pinned, signed/local image or pinned package version; never deploy `latest` in production.
- Keep canonical exports backend-neutral and test restore into a clean instance.
- Back up canonical records and source references before indexes; verify re-embedding/reindex from canonical data.
- Run with local embeddings by default. A configurable local or remote extraction LLM is acceptable only when data-flow policy is explicit.
- Hindsight (MIT), Mem0 OSS (Apache-2.0), Graphiti (Apache-2.0), Letta Code/APIs (Apache-2.0), Cognee (Apache-2.0), and LangGraph (MIT) are permissively licensed in the researched repositories; service and hosted features may differ.
- Zep Cloud is proprietary/terms-based and local Community Edition is deprecated.
- Supermemory's repository license and documented self-hosted Lite cap must be reconciled before use.
- Fast-moving candidates need compatibility fixtures that replay the common corpus across upgrades.

## 12. Backend-neutral paper interface

This is intentionally a capability boundary, not a vendor-shaped API:

```python
class MemoryBackend(Protocol):
    def add(self, record: MemoryRecord) -> BackendRef: ...
    def get(self, scope: Scope, memory_id: UUID) -> MemoryRecord | None: ...
    def search(self, request: SearchRequest) -> list[SearchHit]: ...
    def update(self, expected_revision: int, record: MemoryRecord) -> BackendRef: ...
    def archive(self, scope: Scope, memory_id: UUID, reason: str) -> BackendRef: ...
    def history(self, scope: Scope, memory_id: UUID) -> list[MemoryRevision]: ...
```

Authentication and authorization do not belong in this backend protocol. The AgentForge service resolves credentials and produces a trusted `Scope`; the adapter never accepts arbitrary caller scope. Search requests include status policy, allowed types, lexical/semantic modes, result/token budgets, and historical inclusion. Search hits include canonical IDs, score components, labels, and source references.

## 13. Rejected and component-only alternatives

- **Zep:** reject for the current local-first boundary; reconsider only if managed cloud and enterprise governance become acceptable.
- **Letta Code runtime:** reject because it replaces/duplicates the existing harness; retain Letta APIs as a backend option.
- **Qdrant and Chroma:** useful vector-store components, not complete memory lifecycle, temporal/provenance, or project authorization systems.
- **LlamaIndex and Haystack:** useful RAG frameworks, but no turnkey server-side AgentForge project policy; component choices only.
- **Mimir:** interesting self-hosted MCP memory, but insufficient evidence of mature scoped authorization, migration guarantees, and production stability.
- **Cognee:** retain as secondary graph/RAG spike; it does not beat the finalist pair on simplicity/security evidence.
- **Supermemory:** retain on watch list until license cap, scoped credentials, export, provenance, and stability are proven.

## 14. Risks and decision gates

| Risk | Consequence | Required mitigation |
|---|---|---|
| Namespace mistaken for ACL | Cross-project data disclosure | Gateway authorization plus adversarial direct/bulk/MCP tests; RLS where applicable. |
| LLM extraction changes meaning | Hypothesis becomes fact; evidence lost | Proposed-by-default state, source refs, human/deterministic validation, evaluation corpus. |
| Supersession handled as deletion | Historical reasoning disappears | Immutable revisions, validity/status fields, historical query mode. |
| Hybrid ranking hides exact code tokens | Repeated failures or missed identifiers | Lexical + semantic retrieval, exact ID lookup, score inspection, benchmark queries. |
| Backend lock-in | Costly migration and broken memory | Canonical AgentForge schema, backend refs separated, export/restore test. |
| Pre-1.0/API churn | Operational breakage | Pin versions, compatibility tests, migrations in staging, rollback plan. |
| Local model footprint/latency | Poor developer experience | Measure full/slim deployments, support remote configurable provider, expose health/latency. |
| Concurrent agent writes | Lost decisions or last-write-wins | Revision preconditions, append-only history, conflict tests. |
| Global promotion poisoning | Untrusted local claim becomes global truth | Proposal queue, separate permission, reviewer identity, audit record. |

### Go/no-go sequence before production implementation

1. Run the common harness against pinned Hindsight and Mem0 OSS local instances.
2. Reject any candidate that cannot be placed behind the exact A/B/global/admin boundary.
3. Compare retrieval quality, provenance reachability, temporal behavior, token usage, latency, and offline operation.
4. Exercise backup/export, clean restore, reindex, and version upgrade/rollback.
5. Select Hindsight only if it passes **every** gate and beats or matches Mem0 on failure/current-decision retrieval.
6. Select Mem0 only if it independently passes **every** gate and Hindsight either fails a gate or loses the measured trade-off.
7. If neither finalist passes, test Graphiti behind the same canonical/security boundary only when its temporal/provenance gain could justify the extra graph service; otherwise choose the custom PostgreSQL baseline.

## 15. Final recommendation

```text
Provisional recommended AgentForge memory architecture (pending mandatory spikes):

Core backend:
    AgentForge canonical PostgreSQL tables plus a Hindsight-derived retrieval
    projection, if and only if Hindsight passes every common
    security/quality/operations gate. Mem0 OSS is a second finalist, not an
    automatic fallback, and must independently pass the same gates.

Integration:
    WRAP

Why:
    Hindsight is the closest paper fit to durable agent memory,
    temporal/graph/keyword retrieval, token budgeting, portability, and
    existing coding-agent integration. Wrapping preserves AgentForge's
    project-aware trust boundary and avoids rebuilding retrieval first.

AgentForge must still own:
    - project/admin identities, credentials, authorization, and audit policy
    - project + global composition and global promotion
    - the canonical typed/statused memory envelope
    - provenance acceptance and source-fragment access
    - validation, supersession, contradiction, and archival rules
    - deterministic mandatory context and token budgets
    - backend-neutral export, backup/restore orchestration, and evaluation

Candidate provides:
    - durable memory storage and APIs
    - semantic, keyword, graph, and temporal retrieval
    - extraction/consolidation primitives
    - bank namespaces and coding-agent integrations
    - local deployment and PostgreSQL-backed persistence
    - token-bounded recall, export/import, and extension hooks

Rejected alternatives:
    - Zep: cloud-first; local Community Edition deprecated; governance paid
    - Letta Code: competing agent runtime, though Letta APIs remain viable
    - LangGraph Store: useful component but too much memory/service policy missing
    - custom-only backend: maximum control but avoidable initial build/maintenance
    - Graphiti as primary: excellent temporal component, but more operations and no auth

Main risks:
    - Hindsight is pre-1.0 and fast-moving
    - tenant/project authorization is not yet proven against the required matrix
    - LLM extraction can misclassify engineering evidence
    - local model and PostgreSQL footprint may affect developer experience
    - canonical lifecycle semantics remain AgentForge responsibility

Proof still needed before implementation:
    - Hindsight versus Mem0 A/B/global/admin adversarial security spike
    - common memory-quality, exact-token, provenance, and temporal corpus
    - token/latency/offline benchmark with local providers
    - concurrent-write and crash-recovery tests
    - export, clean restore, reindex, and pinned-version upgrade/rollback
```

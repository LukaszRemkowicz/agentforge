"""Reproduce the AgentForge LangGraph Store Task 0 smoke test.

Tested with Python 3.12, langgraph 1.2.12, langgraph-checkpoint 4.2.0,
langgraph-checkpoint-postgres 3.1.2, and langchain-core 1.6.6.
"""

from __future__ import annotations

import json
import math
import re
import time
from typing import Iterable

from langchain_core.embeddings import Embeddings
from langgraph.store.memory import InMemoryStore


TERMS = [
    "brightness",
    "sparse",
    "subset",
    "failed",
    "failure",
    "condition",
    "long",
    "range",
    "neighbour",
    "descriptor",
    "astrometry",
    "mandatory",
    "optional",
    "repeat",
    "experiment",
    "evidence",
]


class KeywordEmbeddings(Embeddings):
    """Deterministic embedder for API behavior, not retrieval benchmarking."""

    def _embed(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z]+", text.lower())
        aliases = {
            "failing": "failed",
            "failures": "failure",
            "neighbor": "neighbour",
        }
        tokens = [aliases.get(token, token) for token in tokens]
        vector = [float(tokens.count(term)) for term in TERMS]
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def render(items: Iterable[object]) -> list[dict]:
    return [
        {
            "namespace": list(item.namespace),
            "key": item.key,
            "score": round(item.score or 0.0, 4),
            "type": item.value["type"],
            "status": item.value["status"],
            "text": item.value["text"],
            "provenance": item.value["provenance"],
        }
        for item in items
    ]


store = InMemoryStore(
    index={
        "dims": len(TERMS),
        "embed": KeywordEmbeddings(),
        "fields": ["text"],
    }
)

records = {
    (("project", "A"), "failure-brightness"): {
        "type": "failure",
        "status": "validated",
        "text": "Brightness-ranked sparse subsets failed under condition X.",
        "provenance": {"report": "experiment-17", "section": "results"},
    },
    (("project", "A"), "hypothesis-neighbour"): {
        "type": "hypothesis",
        "status": "proposed",
        "text": "Long-range neighbour descriptors may avoid the issue.",
        "provenance": {"task": "research-9"},
    },
    (("project", "A"), "decision-astrometry-v1"): {
        "type": "decision",
        "status": "superseded",
        "text": "Astrometry.net is mandatory.",
        "provenance": {"decision": "D-12", "revision": 1},
    },
    (("project", "A"), "decision-astrometry-v2"): {
        "type": "decision",
        "status": "validated",
        "text": "Astrometry.net is optional.",
        "provenance": {
            "decision": "D-12",
            "revision": 2,
            "supersedes": "decision-astrometry-v1",
        },
    },
    (("project", "B"), "private-b"): {
        "type": "finding",
        "status": "validated",
        "text": "Project B private fact.",
        "provenance": {"report": "b-only"},
    },
    (("global",), "anti-repeat"): {
        "type": "rule",
        "status": "validated",
        "text": "Before repeating a failed experiment, retrieve prior failure evidence.",
        "provenance": {"policy": "agentforge-1"},
    },
}

for (namespace, key), value in records.items():
    store.put(namespace, key, value)

for index in range(25):
    store.put(
        ("project", "A"),
        f"distractor-{index:02d}",
        {
            "type": "observation",
            "status": "validated",
            "text": f"Unrelated cache latency observation number {index}.",
            "provenance": {"report": f"cache-{index}"},
        },
    )

manual_text = "\n".join(
    value["text"]
    for (namespace, _), value in records.items()
    if namespace in {("project", "A"), ("global",)}
)
manual_text += "\n" + "\n".join(
    f"Unrelated cache latency observation number {index}." for index in range(25)
)

started = time.perf_counter()
retrieved_for_context = store.search(
    ("project", "A"), query="brightness sparse subset failure", limit=1
)
retrieved_for_context += store.search(
    ("global",), query="repeat failed experiment evidence", limit=1
)
retrieval_ms = (time.perf_counter() - started) * 1000
retrieved_text = "\n".join(item.value["text"] for item in retrieved_for_context)

results = {
    "a_current_decisions": render(
        store.search(
            ("project", "A"),
            query="Astrometry.net",
            filter={"status": "validated"},
        )
    ),
    "a_superseded_inspectable": store.get(
        ("project", "A"), "decision-astrometry-v1"
    ).dict(),
    "a_failure_paraphrase": render(
        store.search(
            ("project", "A"), query="sparse brightness subset failure evidence"
        )
    ),
    "a_global": render(
        store.search(("global",), query="avoid repeating failed experiments")
    ),
    "b_direct_cross_project": store.get(("project", "B"), "private-b").dict(),
    "all_project_prefix_visible_count": len(
        store.search(("project",), query=None, limit=100)
    ),
    "exact_identifier": store.get(
        ("project", "A"), "decision-astrometry-v2"
    ).dict(),
    "token_efficiency_approx": {
        "available_documents": 30,
        "retrieved_chunks": 2,
        "manual_words": len(manual_text.split()),
        "retrieved_words": len(retrieved_text.split()),
        "relevant_results": 2,
        "irrelevant_results": 0,
        "latency_ms": round(retrieval_ms, 3),
        "note": (
            "Synthetic in-memory corpus and deterministic test embedder; "
            "not a production benchmark."
        ),
    },
}

assert results["a_current_decisions"][0]["text"] == "Astrometry.net is optional."
assert results["a_superseded_inspectable"]["value"]["status"] == "superseded"
assert results["a_failure_paraphrase"][0]["key"] == "failure-brightness"
assert results["a_global"][0]["key"] == "anti-repeat"
assert results["b_direct_cross_project"]["key"] == "private-b"
assert results["all_project_prefix_visible_count"] == 30
assert results["exact_identifier"]["key"] == "decision-astrometry-v2"

print(json.dumps(results, indent=2, default=str))

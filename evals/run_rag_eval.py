"""Lightweight RAG evaluation runner.

Usage:
    uv run python evals/run_rag_eval.py

Loads bundled sample documents, runs predefined questions through QueryService,
and checks expected source retrieval and key term presence.
Does not require external API keys.
"""

import json
import sys
from pathlib import Path

# Ensure the project root is on sys.path so that ``from app`` imports work
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.core.config import settings
from app.core.container import embedding_model, llm_client, vector_store
from app.ingestion.pipeline import build_sample_chunks
from app.services.query_service import QueryService


def main() -> int:
    cases_path = Path(__file__).parent / "rag_cases.json"
    cases = json.loads(cases_path.read_text())

    # Ingest samples
    chunks = build_sample_chunks(Path("samples"))
    vectors = embedding_model.embed_documents([c.text for c in chunks])
    vector_store.clear()
    vector_store.add(chunks, vectors)

    qs = QueryService(
        vector_store=vector_store,
        embedding_model=embedding_model,
        llm_client=llm_client,
    )

    results = []
    failures = 0

    for case in cases:
        rid = case["id"]
        response = qs.answer(question=case["question"], top_k=3)

        top_source = response.sources[0].source if response.sources else ""
        source_ok = case["expected_source"] in top_source

        # Check terms in answer or source text
        text = response.answer + " " + " ".join(s.text for s in response.sources)
        text_lower = text.lower()
        term_results = {}
        for term in case["expected_terms"]:
            found = term.lower() in text_lower
            term_results[term] = found

        terms_ok = all(term_results.values())

        passed = source_ok and terms_ok
        if not passed:
            failures += 1

        results.append(
            {
                "id": rid,
                "question": case["question"],
                "passed": passed,
                "source_match": source_ok,
                "top_source": top_source,
                "expected_source": case["expected_source"],
                "term_hits": term_results,
                "terms_all_found": terms_ok,
            }
        )

    # Summary
    print("=" * 60)
    print(f"RAG Evaluation — {len(results)} cases, {failures} failure(s)")
    print("=" * 60)

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']}: {r['question'][:50]}")
        if not r["passed"]:
            if not r["source_match"]:
                print(f"         source: got '{r['top_source']}', "
                      f"expected '{r['expected_source']}'")
            if not r["terms_all_found"]:
                missing = [t for t, ok in r["term_hits"].items() if not ok]
                print(f"         terms missing: {missing}")

    print("=" * 60)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

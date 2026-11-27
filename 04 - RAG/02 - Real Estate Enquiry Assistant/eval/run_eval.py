"""Evaluation for the Real Estate Enquiry Assistant (commit 4 of 5).

Target: Allen5288/AI-Apps-Collection —
  04 - RAG/02 - Real Estate Enquiry Assistant/eval/run_eval.py
Suggested PR title: Real Estate Enquiry Assistant: evaluation golden
  set + eval script (4 of 5)

Runs the golden set in eval/golden.json against POST /ask and scores
the three things the agency cares about:

1. Recall@k — is the listing the question is about in the top-k
   citations? (k = 3 by default, the endpoint default.)
2. Faithfulness — every fact in the answer (price, beds, inspection
   time, agent) comes from a cited listing, and no other listing's
   facts leak in. The answer is composed from the retrieved listings
   only (see answer.py), so this check is exact, not judged by a model.
3. Fallback correctness — questions about properties the agency does
   not have must answer "I could not find a listing..." with no
   citations, never a guessed property.

Usage (from this case folder):
    python eval/run_eval.py [--out eval/runs/2026-11-28.json]

Exit code 0 when all gates pass, 1 otherwise. Gates:
    mean Recall@3 >= 0.80, faithfulness failures == 0,
    fallback correct on every fallback question.

Stdlib + FastAPI's TestClient (which needs httpx, the TestClient
dependency — `pip install httpx` — not an app dependency). If httpx
is missing, the script falls back to calling the endpoint function
directly, which runs the same retriever + composer code minus HTTP
serialisation. No new app dependencies, no API keys, no LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CASE_DIR))

from answer import format_price  # noqa: E402  (needs CASE_DIR on sys.path)

GOLDEN_PATH = CASE_DIR / "eval" / "golden.json"
LISTINGS_PATH = CASE_DIR / "data" / "listings.json"

MIN_MEAN_RECALL = 0.80

MONEY_RE = re.compile(r"\$[\d,]+")
BED_RE = re.compile(r"(\d+) bed")
INSPECTION_RE = re.compile(r"Next inspection: (.+)")
AGENT_RE = re.compile(r"Agent: (.+)")


def recall_at_k(expected: list[str], cited: list[str], k: int) -> float:
    """Fraction of the expected listing ids present in the top-k."""
    if not expected:
        return 1.0  # fallback question: nothing to retrieve
    found = set(expected) & set(cited[:k])
    return len(found) / len(expected)


def check_faithfulness(answer: str, citations: list[dict],
                       by_id: dict[str, dict]) -> list[str]:
    """Every fact in the answer must come from a cited listing.

    Returns a list of failure messages; empty means faithful.
    Works because answer.py composes the answer from the retrieved
    listings only — a templated answer can be checked exactly.
    """
    failures: list[str] = []
    cited_ids = [c["id"] for c in citations]
    cited_listings = [by_id[i] for i in cited_ids if i in by_id]

    if not cited_listings:
        return failures  # fallback answers have no facts to check

    # Every cited listing's address and price must appear (the answer
    # claims to be about these listings, so it must actually name them).
    for item in cited_listings:
        if item["address"] not in answer:
            failures.append(f"cited {item['id']} address not in answer")
        if format_price(item).split(" per week")[0] not in answer:
            failures.append(f"cited {item['id']} price not in answer")

    # Every dollar figure in the answer must be a cited listing's price.
    cited_prices = {f"${item['price']:,}" for item in cited_listings}
    for money in MONEY_RE.findall(answer):
        if money not in cited_prices:
            failures.append(f"price {money} is not a cited listing's price")

    # Every bed count must be a cited listing's bed count.
    cited_beds = {str(item["beds"]) for item in cited_listings}
    for beds in BED_RE.findall(answer):
        if beds not in cited_beds:
            failures.append(f"{beds} bed is not a cited listing's bed count")

    # Every inspection time and agent name must belong to a cited listing.
    cited_inspections = {item.get("inspection") for item in cited_listings}
    for inspection in INSPECTION_RE.findall(answer):
        if inspection.strip() not in cited_inspections:
            failures.append(f"inspection {inspection!r} is not a cited listing's")

    cited_agents = {item["agent"] for item in cited_listings}
    for agent in AGENT_RE.findall(answer):
        if agent.strip() not in cited_agents:
            failures.append(f"agent {agent!r} is not a cited listing's agent")

    # No other listing's facts may leak in: a wrong address or price
    # in the answer is a hallucination even if the cited facts are right.
    for item_id, item in by_id.items():
        if item_id in cited_ids:
            continue
        if item["address"] in answer:
            failures.append(f"non-cited listing {item_id} address in answer")
        if f"${item['price']:,}" in answer:
            failures.append(f"non-cited listing {item_id} price in answer")

    return failures


def call_ask(client, body: dict) -> dict:
    """POST /ask, via TestClient or — if httpx is missing — by calling
    the endpoint function directly (same retriever + composer code)."""
    if client is not None:
        response = client.post("/ask", json=body)
        response.raise_for_status()
        return response.json()
    from app import AskRequest, ask

    return ask(AskRequest(**body)).model_dump()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the golden-set eval.")
    parser.add_argument("--out", help="Write the per-question results as JSON")
    args = parser.parse_args()

    golden = json.loads(GOLDEN_PATH.read_text())
    questions = golden["questions"]
    listings = json.loads(LISTINGS_PATH.read_text())
    by_id = {item["id"]: item for item in listings}

    try:
        from fastapi.testclient import TestClient

        from app import app

        client = TestClient(app)
    except ImportError:
        print("[eval] httpx not installed — calling the endpoint "
              "function directly (same code path, no HTTP layer). "
              "Run `pip install httpx` to test over HTTP instead.")
        client = None

    recalls: list[float] = []
    top1_correct = 0
    answerable = 0
    fallback_ok = 0
    fallback_total = 0
    faithfulness_failures = 0
    results = []

    for row in questions:
        body = {"question": row["question"], "top_k": row.get("top_k", 3)}
        body.update(row.get("filters", {}))
        payload = call_ask(client, body)
        cited = [c["id"] for c in payload["citations"]]
        answer = payload["answer"]

        entry = {"question": row["question"], "cited": cited,
                 "fallback": payload["fallback"]}
        if row.get("fallback"):
            fallback_total += 1
            ok = payload["fallback"] and not cited
            fallback_ok += 1 if ok else 0
            entry["recall"] = 1.0 if ok else 0.0
            status = "PASS" if ok else "FAIL fallback"
            print(f"{status}  fallback  {row['question']}")
        else:
            answerable += 1
            score = recall_at_k(row["expected"], cited, body["top_k"])
            recalls.append(score)
            if cited[:1] == row["expected"]:
                top1_correct += 1
            entry["recall"] = score
            entry["expected"] = row["expected"]
            status = "PASS" if score == 1.0 else "FAIL recall"
            print(f"{status}  recall@{body['top_k']}={score:.2f}  "
                  f"expected {row['expected']} cited {cited}  "
                  f"{row['question']}")

        problems = check_faithfulness(answer, payload["citations"], by_id)
        for forbidden in row.get("must_not", []):
            if forbidden in answer:
                problems.append(f"must-not {forbidden!r} appears in answer")
        if problems:
            faithfulness_failures += len(problems)
            for problem in problems:
                print(f"  FAITHFULNESS FAIL: {problem}")
        entry["faithfulness_failures"] = problems
        results.append(entry)

    mean_recall = sum(recalls) / len(recalls) if recalls else 1.0
    print(f"\nAnswerable questions: {answerable}")
    print(f"Mean Recall@3: {mean_recall:.2f} "
          f"(top-1 correct {top1_correct}/{answerable})")
    print(f"Fallback correct: {fallback_ok}/{fallback_total}")
    print(f"Faithfulness failures: {faithfulness_failures}")

    gates = [
        ("mean Recall@3 >= 0.80", mean_recall >= MIN_MEAN_RECALL),
        ("faithfulness failures == 0", faithfulness_failures == 0),
        ("fallback correct on all fallback questions",
         fallback_ok == fallback_total),
    ]
    failed = [name for name, ok in gates if not ok]
    for name, ok in gates:
        print(f"  {'PASS' if ok else 'FAIL'}  gate: {name}")
    if failed:
        print(f"\nEVAL FAILED: {len(failed)} gate(s) failed")
    else:
        print("\nEVAL PASSED: all gates green")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(
            {"mean_recall": round(mean_recall, 3),
             "top1_correct": top1_correct,
             "answerable": answerable,
             "fallback": f"{fallback_ok}/{fallback_total}",
             "faithfulness_failures": faithfulness_failures,
             "gates_passed": not failed,
             "results": results},
            indent=2))
        print(f"Results written to {out_path}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

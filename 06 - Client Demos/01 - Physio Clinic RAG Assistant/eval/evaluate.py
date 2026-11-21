"""Golden evaluation for the Physio Clinic RAG Assistant (concept demo).

Run from this case folder:

    python eval/evaluate.py

For each of the 10 patient FAQs, the check is: does the answer cite the
expected source document, and does it contain the expected key fact?
One extra out-of-scope question checks the abstention rule: the answer
must say it is not in the documents and must cite no source.

This uses only the standard library plus app/rag.py, so no LLM key
is needed to run it. Exit code 0 means every check passed.
"""

from __future__ import annotations

import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CASE_DIR))

from app.rag import Retriever

GOLDEN = [
    {"question": "What are your opening hours on Saturday?", "expected_source": "prices-and-hours.md", "must_contain": "8:00 am"},
    {"question": "How much does an initial consultation cost?", "expected_source": "prices-and-hours.md", "must_contain": "$95"},
    {"question": "Do you bulk bill?", "expected_source": "bulk-billing.md", "must_contain": "do not bulk bill"},
    {"question": "Can I claim physiotherapy on my private health insurance?", "expected_source": "bulk-billing.md", "must_contain": "private health"},
    {"question": "Do I need a GP referral to book?", "expected_source": "faqs.md", "must_contain": "do not need a GP referral"},
    {"question": "What exercises are on the lower back handout?", "expected_source": "exercise-handouts.md", "must_contain": "pelvic tilt"},
    {"question": "Do you treat sports injuries?", "expected_source": "services.md", "must_contain": "sports physiotherapy"},
    {"question": "How do I cancel my appointment, and is there a fee?", "expected_source": "faqs.md", "must_contain": "$40"},
    {"question": "Do you offer telehealth appointments?", "expected_source": "faqs.md", "must_contain": "telehealth"},
    {"question": "What should I bring to my first appointment?", "expected_source": "services.md", "must_contain": "referral letter"},
    {"question": "What is my MRI result?", "expected_source": None, "must_contain": "not in our documents"},
]


def main() -> int:
    retriever = Retriever(CASE_DIR / "data")
    passed = 0
    for i, case in enumerate(GOLDEN, start=1):
        result = retriever.answer(case["question"])
        answer = result["answer"].lower()
        if case["expected_source"] is None:
            ok = (not result["answered"] and not result["sources"] and case["must_contain"] in answer)
        else:
            ok = (case["expected_source"] in result["sources"] and case["must_contain"] in answer)
        passed += 1 if ok else 0
        status = "PASS" if ok else "FAIL"
        print(str(i) + ". " + status + "  " + case["question"] + "  -> sources=" + str(result["sources"]) + " score=" + str(result["score"]))
    print("")
    print(str(passed) + "/" + str(len(GOLDEN)) + " golden checks passed.")
    return 0 if passed == len(GOLDEN) else 1


if __name__ == "__main__":
    raise SystemExit(main())

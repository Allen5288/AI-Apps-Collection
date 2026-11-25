"""Answer composition for the Real Estate Enquiry Assistant.

Stdlib only — no LLM key needed. Takes the retriever's top-k
listings and composes a grounded answer: every fact in the answer
comes from a retrieved listing, and every listing cited is one the
retriever actually returned. When nothing matches, the answer says
so instead of inventing a property.

The LLM step (commit 5) will replace `compose_answer`'s template
with a provider call — same inputs (query + retrieved listings),
same outputs (answer + citations + fallback), same contract.
"""

from __future__ import annotations


def format_price(listing: dict) -> str:
    if listing["price_type"] == "rent":
        return f"${listing['price']:,} per week"
    return f"${listing['price']:,}"


def compose_answer(query: str, results: list[dict]) -> dict:
    """Build the answer dict for a question.

    Returns {"answer": str, "citations": [...], "fallback": bool}.
    `fallback` is True when no listing matched — the answer then
    says so plainly and lists nothing.
    """
    if not results:
        return {
            "answer": (
                "I could not find a listing in our current properties "
                "that matches that question. If you tell me the suburb, "
                "budget and number of bedrooms, I can check again — or "
                "leave your details and an agent will call you back."
            ),
            "citations": [],
            "fallback": True,
        }

    lines = [
        "Here is what I found in our current listings:",
        "",
    ]
    citations = []
    for i, result in enumerate(results, start=1):
        item = result["listing"]
        citations.append(
            {
                "n": i,
                "id": item["id"],
                "address": f"{item['address']}, {item['suburb']}",
                "score": result["score"],
            }
        )
        lines.append(
            f"[{i}] {item['address']}, {item['suburb']} — "
            f"{format_price(item)} ({item['status']}) | "
            f"{item['beds']} bed, {item['baths']} bath, "
            f"{item['parking']} car"
        )
        lines.append(f"    {item['description']}")
        if item.get("inspection"):
            lines.append(f"    Next inspection: {item['inspection']}")
        lines.append(f"    Agent: {item['agent']}")
        lines.append("")

    top = results[0]["listing"]
    lines.append(
        f"The closest match is [{1}] {top['address']}, {top['suburb']}. "
        "If you would like to inspect it, I can take your name and "
        "phone number and pass them to the listing agent."
    )
    return {"answer": "\n".join(lines).strip(), "citations": citations, "fallback": False}

"""TF-IDF retriever for the Real Estate Enquiry Assistant.

Stdlib only. Loads data/listings.json, builds one text chunk per
listing, and ranks chunks by TF-IDF cosine similarity. Filters
(suburb, min/max price, min beds, status) apply before ranking, so
a cheap unit in Parramatta never outranks a matching house in
The Ponds.

Usage:
    python retrieval.py "3 bed house in The Ponds under $1.2m"
    python retrieval.py "pet friendly rental" --status rent --top-k 2
    python retrieval.py "apartment near Chatswood station" --suburb Chatswood
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

DATA_PATH = Path(__file__).with_name("data") / "listings.json"

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenise(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def listing_text(listing: dict) -> str:
    parts = [
        listing["address"],
        listing["suburb"],
        listing["type"],
        listing["status"],
        f"{listing['beds']} bed {listing['baths']} bath",
        f"{listing['parking']} car parking",
        listing["description"],
        " ".join(listing.get("features", [])),
        f"agent {listing['agent']}",
    ]
    return " ".join(parts)


class Retriever:
    """Small TF-IDF retriever over listing chunks."""

    def __init__(self, listings: list[dict]):
        self.listings = listings
        self.docs = [tokenise(listing_text(item)) for item in listings]
        self.vocab: dict[str, int] = {}
        for doc in self.docs:
            for token in set(doc):
                self.vocab[token] = self.vocab.get(token, 0) + 1
        self.idf = {
            token: math.log((len(self.docs) + 1) / (df + 1)) + 1.0
            for token, df in self.vocab.items()
        }

    def _vector(self, tokens: list[str]) -> dict[str, float]:
        counts: dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        total = len(tokens) or 1
        return {
            token: (count / total) * self.idf.get(token, 1.0)
            for token, count in counts.items()
        }

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        dot = sum(a[t] * b.get(t, 0.0) for t in a)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 3, **filters) -> list[dict]:
        candidates = [item for item in self.listings if _matches(item, filters)]
        if not candidates:
            return []
        query_vec = self._vector(tokenise(query))
        scored = []
        for item in candidates:
            doc_vec = self._vector(tokenise(listing_text(item)))
            scored.append((self._cosine(query_vec, doc_vec), item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            {"score": round(score, 3), "listing": item}
            for score, item in scored[:top_k]
        ]


def _matches(listing: dict, filters: dict) -> bool:
    if filters.get("suburb") and listing["suburb"].lower() != filters["suburb"].lower():
        return False
    if filters.get("min_price") and listing["price"] < filters["min_price"]:
        return False
    if filters.get("max_price") and listing["price"] > filters["max_price"]:
        return False
    if filters.get("min_beds") and listing["beds"] < filters["min_beds"]:
        return False
    if filters.get("status") and listing["status"] != filters["status"]:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Search synthetic listings.")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--suburb")
    parser.add_argument("--min-price", type=int)
    parser.add_argument("--max-price", type=int)
    parser.add_argument("--min-beds", type=int)
    parser.add_argument("--status", choices=["sale", "rent"])
    args = parser.parse_args()

    listings = json.loads(DATA_PATH.read_text())
    retriever = Retriever(listings)
    results = retriever.search(
        args.query,
        top_k=args.top_k,
        suburb=args.suburb,
        min_price=args.min_price,
        max_price=args.max_price,
        min_beds=args.min_beds,
        status=args.status,
    )
    if not results:
        print("No listings match those filters.")
        return
    for result in results:
        item = result["listing"]
        print(f"[{result['score']:.3f}] {item['address']}, {item['suburb']} — "
              f"${item['price']:,} {item['price_type']} | "
              f"{item['beds']} bed {item['baths']} bath, {item['parking']} car")
        print(f"        {item['description'][:120]}...")


if __name__ == "__main__":
    main()

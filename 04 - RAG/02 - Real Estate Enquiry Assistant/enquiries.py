"""Enquiry capture for the Real Estate Enquiry Assistant.

When the assistant's answer ends with "I can take your name and
phone number", this module is what takes them. POST /enquiries
stores the enquiry as JSON so the listing agent can call the person
back — with the listing and the inspection time attached, so nobody
has to ask "which property was that?".

Rules, kept deliberately small (same discipline as the BookingApi
store in NodeJS-Apps-Collection):

- Validation at the boundary: name, phone, listing and inspection
  are all checked before anything is stored. A bad enquiry gets a
  422, not a row the agent has to clean up by hand.
- The listing must exist, and the inspection must be the one on
  that listing. An enquiry for an inspection that does not exist is
  a wasted call for the agent and a no-show for the buyer.
- Duplicate guard by phone + listing: the same person enquiring
  twice about the same property is one enquiry, not two callbacks.
  The second POST returns 409 with the existing enquiry id.
- The store is a JSON file with atomic writes (temp file + rename),
  the same pattern as the BookingApi. A crash mid-write leaves the
  old file intact. It is a file, not a database, because the agency
  takes dozens of enquiries a day — the day that stops being true,
  this store is the seam to replace (SQLite, same record shape).
- The listing address and agent name are snapshotted into the
  enquiry. If the listing changes later, the enquiry still says
  which property the person asked about.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
DATA_FILE = DATA_DIR / "enquiries.json"

# Australian mobile, after stripping spaces, dashes and brackets:
# 04XX XXX XXX, or +61 4XX XXX XXX. Landlines are not accepted —
# the agent calls the person back, and a mobile is what they answer.
_MOBILE_RE = re.compile(r"^(\+61|0)4\d{8}$")


def normalise_phone(raw: str) -> str:
    """Strip spaces, dashes and brackets. '+61 400 000 000' and
    '0400 000 000' become '+61400000000' and '0400000000'."""
    return re.sub(r"[\s\-()]", "", raw)


def validate_enquiry(body: dict, listings: list[dict]) -> dict:
    """Validate an enquiry body. Returns the cleaned record fields,
    or raises ValueError with a human-readable message.

    `body` is the raw JSON object; `listings` is the agency's
    listings (same file the retriever reads), so the checks always
    agree with what the assistant can answer about.
    """
    name = body.get("name")
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 100:
        raise ValueError("name is required (2-100 characters)")

    phone_raw = body.get("phone")
    if not isinstance(phone_raw, str):
        raise ValueError("phone is required")
    phone = normalise_phone(phone_raw)
    if not _MOBILE_RE.match(phone):
        raise ValueError(
            "phone must be an Australian mobile, e.g. 0400 000 000"
        )

    listing_id = body.get("listing_id")
    listing = next(
        (item for item in listings if item["id"] == listing_id), None
    )
    if listing is None:
        raise ValueError(f"no listing with id {listing_id!r}")

    inspection = body.get("inspection")
    if inspection != listing.get("inspection"):
        raise ValueError(
            "inspection must match the listing's inspection time: "
            f"{listing.get('inspection')!r}"
        )

    message = body.get("message")
    if message is not None and (
        not isinstance(message, str) or len(message) > 500
    ):
        raise ValueError("message must be at most 500 characters")

    return {
        "name": name.strip(),
        "phone": phone,
        "listing_id": listing["id"],
        "listing_address": f"{listing['address']}, {listing['suburb']}",
        "agent": listing["agent"],
        "inspection": inspection,
        "message": (message or "").strip(),
    }


def load_enquiries() -> list[dict]:
    """Load all enquiries. A missing file means first run (empty
    list); a corrupt file logs a warning and starts empty, leaving
    the corrupt file in place for a human to inspect."""
    try:
        parsed = json.loads(DATA_FILE.read_text())
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[enquiries] could not load {DATA_FILE} ({exc}) — starting empty")
        return []
    if not isinstance(parsed, list):
        print(f"[enquiries] {DATA_FILE} is not a list — starting empty")
        return []
    return parsed


def _save(enquiries: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = DATA_FILE.with_suffix(".json.tmp")
    tmp_file.write_text(json.dumps(enquiries, indent=2))
    tmp_file.rename(DATA_FILE)  # atomic on the same filesystem


def create_enquiry(cleaned: dict, enquiries: list[dict]) -> tuple[dict, bool]:
    """Store a validated enquiry. Returns (record, created): on a
    duplicate phone + listing the existing record is returned with
    created=False, and nothing is written — the caller turns that
    into a 409."""
    existing = next(
        (
            item
            for item in enquiries
            if item["phone"] == cleaned["phone"]
            and item["listing_id"] == cleaned["listing_id"]
        ),
        None,
    )
    if existing is not None:
        return existing, False
    record = {
        "id": str(uuid.uuid4()),
        "status": "new",
        **cleaned,
    }
    enquiries.append(record)
    _save(enquiries)
    return record, True

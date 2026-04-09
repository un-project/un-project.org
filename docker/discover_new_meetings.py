#!/usr/bin/env python3
"""Discover new UN meeting verbatim records and download their PDFs.

Probes the UN Documents API incrementally from the last known GA and SC
meeting numbers to find documents published since the last ingest run.

Outputs
-------
- $WORK_DIR/new_symbols.txt   one symbol per line (only successfully downloaded)
- $WORK_DIR/pdfs/<slug>.pdf   downloaded PDF for each symbol

Environment
-----------
WORK_DIR     scratch directory (default: /tmp/ingest)
MAX_PROBE    how many consecutive misses before stopping (default: 5)
REQUEST_DELAY_S  seconds between API probes (default: 1.0)
"""

from __future__ import annotations

import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── Django setup (for DB queries) ───────────────────────────────────────────
sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "un_site.settings")
import django  # noqa: E402
django.setup()
from django.db import connection  # noqa: E402

# ── Config ───────────────────────────────────────────────────────────────────
WORK_DIR = Path(os.environ.get("WORK_DIR", "/tmp/ingest"))
PDF_DIR = WORK_DIR / "pdfs"
SYMBOLS_FILE = WORK_DIR / "new_symbols.txt"
MAX_PROBE = int(os.environ.get("MAX_PROBE", "5"))
DELAY = float(os.environ.get("REQUEST_DELAY_S", "1.0"))

# UN Documents API: returns the PDF directly when the symbol exists.
# HTTP 200 → document exists and is downloadable.
# HTTP 404 / 400 → document does not exist.
_API = "https://documents.un.org/api/symbol/access?s={symbol}&l=en&t=pdf"
_UA = "un-ingest/1.0 (research; github.com/cravesoft/un-project.org)"

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
    stream=sys.stdout,
)


# ── UN Documents API helpers ─────────────────────────────────────────────────

def _request(symbol: str, timeout: int) -> urllib.request.addinfourl | None:
    url = _API.format(symbol=urllib.parse.quote(symbol, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError:
        return None
    except OSError as exc:
        log.debug("Network error for %s: %s", symbol, exc)
        return None


def probe(symbol: str) -> bool:
    """Return True if the document PDF is available."""
    resp = _request(symbol, timeout=20)
    if resp is not None:
        resp.close()
        return True
    return False


def download(symbol: str, dest: Path) -> bool:
    """Download the PDF for *symbol* to *dest*. Return True on success."""
    resp = _request(symbol, timeout=120)
    if resp is None:
        return False
    try:
        dest.write_bytes(resp.read())
        return dest.stat().st_size > 1024  # reject suspiciously small responses
    except OSError as exc:
        log.warning("Write error for %s: %s", symbol, exc)
        return False
    finally:
        resp.close()


def slug(symbol: str) -> str:
    return symbol.replace("/", "-").replace(".", "-")


# ── Database helpers ─────────────────────────────────────────────────────────

def latest_ga() -> tuple[int, int]:
    """Return (session, max_pv_number) of the latest GA PV in the database."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT session,
                   MAX(CAST(split_part(symbol, '.', 2) AS INTEGER))
            FROM documents
            WHERE symbol ~ '^A/[0-9]+/PV\\.[0-9]+$'
              AND session IS NOT NULL
            GROUP BY session
            ORDER BY session DESC
            LIMIT 1
        """)
        row = cur.fetchone()
    if row:
        return int(row[0]), int(row[1])
    return 79, 0  # safe fallback


def latest_sc() -> int:
    """Return the max PV number of SC meetings in the database."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT MAX(CAST(split_part(symbol, '.', 2) AS INTEGER))
            FROM documents
            WHERE symbol ~ '^S/PV\\.[0-9]+$'
        """)
        row = cur.fetchone()
    return int(row[0]) if row and row[0] else 9000  # safe fallback


def already_imported(symbols: list[str]) -> set[str]:
    """Return the subset of *symbols* already present in the documents table."""
    if not symbols:
        return set()
    with connection.cursor() as cur:
        cur.execute(
            "SELECT symbol FROM documents WHERE symbol = ANY(%s)",
            [symbols],
        )
        return {row[0] for row in cur.fetchall()}


# ── Discovery ────────────────────────────────────────────────────────────────

def _probe_sequence(make_symbol, start: int) -> list[str]:
    """Probe make_symbol(n) for n = start, start+1, ... stopping after
    MAX_PROBE consecutive misses."""
    found: list[str] = []
    misses = 0
    n = start
    while misses < MAX_PROBE:
        sym = make_symbol(n)
        if probe(sym):
            log.info("  Found: %s", sym)
            found.append(sym)
            misses = 0
        else:
            misses += 1
        time.sleep(DELAY)
        n += 1
    return found


def discover() -> list[str]:
    """Return new document symbols not yet in the database."""
    found: list[str] = []

    # General Assembly — sequential within each session
    ga_session, ga_last = latest_ga()
    log.info("Latest GA in DB: A/%d/PV.%d", ga_session, ga_last)
    found += _probe_sequence(
        lambda n, s=ga_session: f"A/{s}/PV.{n}",
        ga_last + 1,
    )
    # Also check if a new GA session has started (begins each September)
    next_session = ga_session + 1
    new_session_docs = _probe_sequence(
        lambda n, s=next_session: f"A/{s}/PV.{n}",
        1,
    )
    if new_session_docs:
        log.info("New GA session %d detected.", next_session)
        found += new_session_docs

    # Security Council — globally sequential
    sc_last = latest_sc()
    log.info("Latest SC in DB: S/PV.%d", sc_last)
    found += _probe_sequence(
        lambda n: f"S/PV.{n}",
        sc_last + 1,
    )

    # Filter out anything already in the DB (handles re-runs)
    imported = already_imported(found)
    if imported:
        log.info("Skipping %d already-imported symbol(s): %s", len(imported), sorted(imported))
    return [s for s in found if s not in imported]


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    log.info("=== Discovering new UN meeting documents ===")
    new_symbols = discover()
    if not new_symbols:
        log.info("No new documents found.")
        sys.exit(0)

    log.info("=== Downloading %d PDF(s) ===", len(new_symbols))
    downloaded: list[str] = []
    for sym in new_symbols:
        dest = PDF_DIR / f"{slug(sym)}.pdf"
        log.info("  %s → %s", sym, dest.name)
        if download(sym, dest):
            downloaded.append(sym)
            log.info("  OK (%d bytes)", dest.stat().st_size)
        else:
            log.warning("  FAILED — skipping %s", sym)
        time.sleep(DELAY)

    if not downloaded:
        log.info("No PDFs downloaded successfully.")
        sys.exit(0)

    SYMBOLS_FILE.write_text("\n".join(downloaded) + "\n")
    log.info("Wrote %d symbol(s) to %s", len(downloaded), SYMBOLS_FILE)


if __name__ == "__main__":
    main()

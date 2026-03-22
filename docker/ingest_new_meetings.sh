#!/usr/bin/env bash
# docker/ingest_new_meetings.sh
#
# Stub for the automated UN meeting ingestion pipeline.
# Runs nightly from the cron container; see docker/crontab.
#
# Full pipeline (once un-extractor is integrated):
#   1. Query the UN ODS API for PV documents published in the last LOOKBACK_DAYS
#   2. Skip symbols already present in the database
#   3. Download each new PDF from the UN document portal
#   4. Run un-extractor to produce meeting_*.json files
#   5. Import JSON into the database (idempotent)
#   6. Deduplicate country rows
#   7. Populate missing ISO codes / flags
#   8. Refresh the full-text search index
#
# Environment variables (inherited from Docker / .env):
#   DATABASE_URL  — postgresql://user:pass@host:port/dbname
#   UN_EXTRACTOR  — path to the un-extractor repo (default: /un-extractor)
#   LOOKBACK_DAYS — how many days back to search for new documents (default: 3)
#   WORK_DIR      — scratch directory for PDFs and JSON (default: /tmp/ingest)

set -euo pipefail

DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER:-myuser}:${DB_PASSWORD:-mypassword}@${DB_HOST:-db}:${DB_PORT:-5432}/${DB_NAME:-unproject}}"
UN_EXTRACTOR="${UN_EXTRACTOR:-/un-extractor}"
LOOKBACK_DAYS="${LOOKBACK_DAYS:-3}"
WORK_DIR="${WORK_DIR:-/tmp/ingest}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }

# ── 1. Discover new documents ────────────────────────────────────────────────
#
# TODO: implement ODS polling.
# The UN ODS API endpoint for document search is not yet stable/documented
# for public use. Options:
#   a) https://documents.un.org/api/documents?symbol=A%2F*%2FPV.*&...
#   b) Scrape https://undocs.org/en/A/78/PV.* incrementally by meeting number
#   c) RSS feed from the UN document portal (if available)
#
# Expected output: one document symbol per line written to $WORK_DIR/new_symbols.txt
# Example:  A/79/PV.42
#           S/PV.9612

log "Step 1: discover — NOT YET IMPLEMENTED"
log "  Populate $WORK_DIR/new_symbols.txt with new document symbols to proceed."
mkdir -p "$WORK_DIR"

if [[ ! -f "$WORK_DIR/new_symbols.txt" ]] || [[ ! -s "$WORK_DIR/new_symbols.txt" ]]; then
    log "No new symbols found (or discovery not implemented). Exiting."
    exit 0
fi

mapfile -t SYMBOLS < "$WORK_DIR/new_symbols.txt"
log "Found ${#SYMBOLS[@]} new symbol(s): ${SYMBOLS[*]}"

# ── 2. Filter out symbols already in the database ────────────────────────────
NEW_SYMBOLS=()
for sym in "${SYMBOLS[@]}"; do
    count=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM documents WHERE symbol = '$sym'")
    if [[ "$count" -eq 0 ]]; then
        NEW_SYMBOLS+=("$sym")
    else
        log "  Skipping $sym (already in database)"
    fi
done

if [[ ${#NEW_SYMBOLS[@]} -eq 0 ]]; then
    log "All symbols already imported. Exiting."
    exit 0
fi

# ── 3. Download PDFs ─────────────────────────────────────────────────────────
#
# TODO: implement PDF download.
# URL pattern: https://documents.un.org/doc/UNDOC/GEN/<path>/<file>.pdf
# The exact URL must be resolved from the ODS API response in step 1.

PDF_DIR="$WORK_DIR/pdfs"
mkdir -p "$PDF_DIR"

log "Step 3: download — NOT YET IMPLEMENTED"
log "  Download PDFs for: ${NEW_SYMBOLS[*]}"
log "  Place files in $PDF_DIR/<symbol>.pdf and re-run."
exit 0

# ── 4. Extract PDFs via un-extractor ─────────────────────────────────────────
JSON_DIR="$WORK_DIR/json"
mkdir -p "$JSON_DIR"

if [[ ! -f "$UN_EXTRACTOR/extract_pdf.py" ]]; then
    log "ERROR: un-extractor not found at $UN_EXTRACTOR"
    exit 1
fi

log "Step 4: extract"
for sym in "${NEW_SYMBOLS[@]}"; do
    pdf="$PDF_DIR/${sym//\//-}.pdf"
    if [[ ! -f "$pdf" ]]; then
        log "  WARNING: PDF not found for $sym, skipping"
        continue
    fi
    log "  Extracting $sym"
    python "$UN_EXTRACTOR/extract_pdf.py" "$pdf" -o "$JSON_DIR/" || log "  WARNING: extraction failed for $sym"
done

# ── 5. Import JSON into the database ─────────────────────────────────────────
log "Step 5: import"
python "$UN_EXTRACTOR/import_json_to_db.py" "$JSON_DIR/" --db "$DATABASE_URL"

# ── 6. Deduplicate country rows ───────────────────────────────────────────────
log "Step 6: deduplicate countries"
python "$UN_EXTRACTOR/fix_country_duplicates.py" --db "$DATABASE_URL"

# ── 7. Populate ISO codes and flags ──────────────────────────────────────────
log "Step 7: populate ISO codes and flags"
cd /app && DB_HOST="${DB_HOST:-db}" python scripts/populate_iso_and_flags.py

# ── 8. Refresh full-text search index ────────────────────────────────────────
log "Step 8: refresh search index"
cd /app && python manage.py refresh_search_index --full

log "Ingestion complete."
rm -rf "$WORK_DIR"

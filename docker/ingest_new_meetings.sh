#!/usr/bin/env bash
# docker/ingest_new_meetings.sh
#
# Automated UN meeting ingestion pipeline.
# Runs nightly from the cron container; see docker/crontab.
#
# Pipeline:
#   1. Discover new PV documents via the UN Documents API and download PDFs
#   2. Run un-extractor to produce meeting_*.json files
#   3. Import JSON into the database (idempotent)
#   4. Deduplicate country rows
#   5. Populate missing ISO codes / flags
#   6. Refresh the full-text search index
#
# Environment variables (inherited from Docker / .env):
#   DATABASE_URL  — postgresql://user:pass@host:port/dbname
#   UN_EXTRACTOR  — path to the un-extractor repo (default: /un-extractor)
#   WORK_DIR      — scratch directory for PDFs and JSON (default: /tmp/ingest)
#   MAX_PROBE     — consecutive API misses before stopping search (default: 5)
#   REQUEST_DELAY_S — seconds between API probes (default: 1.0)

set -euo pipefail

DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER:-myuser}:${DB_PASSWORD:-mypassword}@${DB_HOST:-db}:${DB_PORT:-5432}/${DB_NAME:-unproject}}"
UN_EXTRACTOR="${UN_EXTRACTOR:-/un-extractor}"
WORK_DIR="${WORK_DIR:-/tmp/ingest}"

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*"; }

# ── 1. Discover new documents and download PDFs ──────────────────────────────

log "Step 1: discover and download"
python /app/docker/discover_new_meetings.py

SYMBOLS_FILE="$WORK_DIR/new_symbols.txt"

if [[ ! -f "$SYMBOLS_FILE" ]] || [[ ! -s "$SYMBOLS_FILE" ]]; then
    log "No new documents. Exiting."
    exit 0
fi

mapfile -t NEW_SYMBOLS < "$SYMBOLS_FILE"
log "New symbols: ${NEW_SYMBOLS[*]}"

# ── 2. Extract PDFs via un-extractor ─────────────────────────────────────────

PROCESS_PDF="$UN_EXTRACTOR/src/pipeline/process_pdf.py"
PDF_DIR="$WORK_DIR/pdfs"
JSON_DIR="$WORK_DIR/json"
mkdir -p "$JSON_DIR"

if [[ ! -f "$PROCESS_PDF" ]]; then
    log "ERROR: un-extractor not found at $UN_EXTRACTOR"
    exit 1
fi

log "Step 2: extract PDFs"
for sym in "${NEW_SYMBOLS[@]}"; do
    pdf="$PDF_DIR/$(echo "$sym" | tr '/' '-' | tr '.' '-').pdf"
    if [[ ! -f "$pdf" ]]; then
        log "  WARNING: PDF not found for $sym ($pdf), skipping"
        continue
    fi
    log "  Extracting $sym"
    python "$PROCESS_PDF" "$pdf" --output "$JSON_DIR/" \
        || log "  WARNING: extraction failed for $sym"
done

# ── 3. Import JSON into the database ─────────────────────────────────────────

log "Step 3: import JSON"
python "$UN_EXTRACTOR/import_json_to_db.py" "$JSON_DIR/" --db "$DATABASE_URL"

# ── 4. Deduplicate country rows ───────────────────────────────────────────────

log "Step 4: deduplicate countries"
python "$UN_EXTRACTOR/scripts/fix_country_duplicates.py" --db "$DATABASE_URL"

# ── 5. Populate ISO codes and flags ──────────────────────────────────────────

log "Step 5: populate ISO codes and flags"
cd /app && DB_HOST="${DB_HOST:-db}" python scripts/populate_iso_and_flags.py

# ── 6. Refresh full-text search index ────────────────────────────────────────

log "Step 6: refresh search index"
cd /app && python manage.py refresh_search_index --full

log "Ingestion complete."
rm -rf "$WORK_DIR"

# UN Project

A web application for exploring United Nations meetings by browsing transcripts, speeches, and voting records from the General Assembly and Security Council.

## Features

- **Meeting transcripts** — full sequential display with speaker attribution and agenda navigation
- **Speech search** — PostgreSQL full-text search across 66,000+ speech segments
- **Country profiles** — representatives, voting history, and speech archive per country; filterable by body (GA/SC) and session
- **Speaker profiles** — speech history and meeting attendance per speaker
- **Voting records** — per-resolution vote tallies and per-country positions
- **Compare countries** — side-by-side voting agreement analysis with cross-matrix and year-by-year breakdown
- **Voting similarity map** — interactive D3 world map coloured by voting alignment; click any country to see most/least similar nations
- **Filters** — browse meetings by body (GA/SC), session, and year

## Quick Start

```bash
docker compose up
```

The app will be available at http://localhost:8000.

On first start, Docker will:
1. Start a PostgreSQL database
2. Run Django migrations (including the full-text search index)
3. Start the web server

### Live development with Watch

```bash
docker compose watch
```

Enables hot-reloading during development: source files, templates, and static assets are synced into the container instantly. Changes to `requirements.txt` or `Dockerfile` trigger a full rebuild. Gunicorn runs with `--reload` so Python changes are picked up automatically.

## Loading Data

The database starts empty. Use [un-extractor](https://github.com/un-project/un-extractor) to extract meeting records from UN documents and import them.

### 1. Extract meeting records

Follow the un-extractor instructions to produce a directory of `meeting_*.json` files (e.g. `output/`).

### 2. Expose the database port

The `db` service must expose port 5432 to localhost. This is already set in `docker-compose.yml`:

```yaml
ports:
  - "5432:5432"
```

Start the database if it isn't running:

```bash
docker compose up db -d
```

### 3. Import the JSON files

From the un-extractor repo directory:

```bash
python import_json_to_db.py /path/to/output/ \
  --db "postgresql://myuser:mypassword@localhost:5432/unproject"
```

The script is idempotent — documents already present in the database are skipped.

### 4. Deduplicate countries

Bulk imports can introduce duplicate country rows (e.g. slightly different spellings of the same delegation name). Run this script from the un-extractor repo first to merge them:

```bash
python fix_country_duplicates.py \
  --db "postgresql://myuser:mypassword@localhost:5432/unproject"
```

**This must be run before step 5.** If duplicate rows exist when ISO codes are assigned, garbage/unmatched rows will race for the same ISO3 code and corrupt country lookups.

### 5. Populate country ISO codes and flags

Countries are imported with only their name. Run this script to fill in ISO2/ISO3 codes and download SVG flags:

```bash
pip install pycountry
DB_HOST=localhost python scripts/populate_iso_and_flags.py
```

This is required for country profiles and the votes page country selector to work.

### 6. Refresh the search index

```bash
docker compose exec web python manage.py refresh_search_index --full
```

The index is also refreshed automatically on every container start.

## Tech Stack

- **Backend:** Django 5.2, PostgreSQL, Django ORM
- **Frontend:** Django templates, plain CSS (no framework)
- **Search:** PostgreSQL full-text search via `django.contrib.postgres`
- **Serving:** Gunicorn + WhiteNoise

## Project Structure

```
un_site/          Django project config (settings, urls)
core/             Homepage and shared template tags
meetings/         Document and DocumentItem models; meeting list/detail views
speeches/         Speech and StageDirection models
countries/        Country model and profile page
speakers/         Speaker model and profile page
votes/            Resolution, Vote, and CountryVote models
search/           Full-text search view and materialized view migration
templates/        HTML templates
static/           CSS and static assets (flags, speaker photos)
```

## URL Structure

| URL | Page |
|-----|------|
| `/` | Homepage — recent meetings and speeches |
| `/meeting/` | Meeting list with filters |
| `/meeting/<slug>/` | Meeting transcript (e.g. `/meeting/A-78-PV-12/`) |
| `/country/<ISO3>/` | Country profile |
| `/speaker/<id>/` | Speaker profile |
| `/votes/` | Voting analysis — country selector, charts, vote table |
| `/votes/compare/` | Compare voting records of two countries |
| `/votes/map/` | Interactive world map of voting similarity |
| `/votes/resolutions/` | Browse all resolutions |
| `/search/?q=...` | Full-text speech search |

Meeting slugs are derived from the UN document symbol by replacing `/` and `.` with `-` (e.g. `A/78/PV.12` → `A-78-PV-12`).

Individual speeches are directly linkable via fragment anchors: `/meeting/A-78-PV-12/#speech-145`.

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | *(required in prod)* | Django secret key |
| `DJANGO_DEBUG` | `false` | Enable debug mode |
| `ALLOWED_HOSTS` | `localhost 127.0.0.1` | Space-separated allowed hosts |
| `DB_NAME` | `unproject` | PostgreSQL database name |
| `DB_USER` | `myuser` | PostgreSQL user |
| `DB_PASSWORD` | `mypassword` | PostgreSQL password |
| `DB_HOST` | `db` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |

## Static Assets

- Country flags: `static/flags/<ISO3>.svg`
- Speaker photos: `static/speakers/<id>.jpg` (optional; hidden if missing)

## Database Schema

The Django models map to a pre-existing PostgreSQL schema:

| Table | Model | Description |
|-------|-------|-------------|
| `countries` | `Country` | UN member states |
| `speakers` | `Speaker` | People who spoke; linked to a country |
| `documents` | `Document` | One row per meeting (symbol, date, session) |
| `document_items` | `DocumentItem` | Agenda items within a meeting |
| `speeches` | `Speech` | One segment per speaker turn |
| `stage_directions` | `StageDirection` | Procedural text between speeches |
| `resolutions` | `Resolution` | Draft and adopted resolutions |
| `votes` | `Vote` | One voting event per resolution per meeting |
| `country_votes` | `CountryVote` | Per-country vote position |

Two materialized views are created by migrations:
- `speech_search_index` — legacy per-speech index (migration 0001)
- `search_index` — unified index covering speeches and resolutions with weighted tsvectors (migration 0002); refreshed automatically on every container startup via `manage.py refresh_search_index`

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

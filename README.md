# UN Project

A web application for exploring United Nations meetings by browsing transcripts, speeches, and voting records from the General Assembly and Security Council.

## Features

- **Meeting transcripts** — full sequential display with speaker attribution and agenda navigation
- **Speech search** — PostgreSQL full-text search across 66,000+ speech segments
- **Country profiles** — representatives, voting history, speech archive, speech frequency chart, and General Debate word cloud; filterable by body (GA/SC) and session
- **Speaker profiles** — speech history and meeting attendance per speaker
- **Speaker list** — searchable and filterable by country at `/speaker/`
- **Voting records** — per-resolution vote tallies, per-country positions, and P5 breakdown on every resolution
- **Voting blocs** — named political groups (NATO, EU, G77, …) and data-driven clusters at `/votes/blocs/`
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

### 7. Fetch speaker photos (optional)

Download Wikipedia portrait photos for UN delegates and save them to `static/speakers/<id>.jpg`:

```bash
python scripts/fetch_speaker_photos.py
```

Speakers are processed in descending order of speech count so the most prominent delegates are handled first. Role-only entries (The President, The Acting President, etc.) are skipped automatically.

The script validates each Wikipedia article before saving: it requires at least one diplomat keyword (minister, ambassador, delegate, …) in the description or extract, rejects non-diplomat matches (athletes, entertainers, …), and checks that the article mentions the speaker's country. A two-phase approach is used: direct title lookup first, then a MediaWiki search API fallback.

Options:

| Flag | Description |
|------|-------------|
| `--force` | Re-download even if the photo already exists |
| `--limit N` | Process at most N speakers (useful for testing) |
| `--dry-run` | Print what would be fetched without saving anything |

Requests are rate-limited to ~4/s. A typical full run (several thousand speakers) takes 20–30 minutes. Re-run after any bulk speaker import to pick up new delegates.

### 8. Compute voting blocs (optional)

Populate the data-driven voting clusters shown on `/votes/blocs/`:

```bash
docker compose exec web python manage.py compute_voting_blocs
```

This runs a pairwise-agreement clustering over 5-year rolling windows and takes a few minutes for the full history. Re-run after any bulk vote import.

## Deployment

The production server runs the same Docker Compose stack.

### Deploying code changes

SSH into the VPS, then:

```bash
git pull
docker compose up --build -d
```

The `web` container automatically runs `migrate` and `collectstatic` on every startup, so
migrations are applied with no extra step.

To follow the logs:

```bash
docker compose logs -f web
```

If static assets don't update, force a rebuild:

```bash
docker compose build --no-cache web
docker compose up -d
```

### Copying the local database to the VPS

Use this when you want to push a freshly-imported local database to production.

**1. Dump the local database:**

```bash
docker compose exec -T db pg_dump -U myuser -d unproject --no-owner --no-acl -Fc > /tmp/unproject.dump
```

**2. Transfer the dump to the VPS:**

```bash
scp unproject.dump user@vps:/path/to/un-project.org/
```

**3. On the VPS, restore into the running container:**

```bash
# Copy the dump into the container
docker compose cp unproject.dump db:/tmp/unproject.dump

# Stop the web container so no queries run during restore
docker compose stop web

# Drop and recreate the database
docker compose exec db psql -U myuser -c "DROP DATABASE IF EXISTS unproject;"
docker compose exec db psql -U myuser -c "CREATE DATABASE unproject;"

# Restore
docker compose exec db pg_restore -U myuser -d unproject \
  --no-owner --no-acl /tmp/unproject.dump

# Restart everything
docker compose start web
```

**4. Refresh the search index** (the materialized views are not included in `pg_dump`):

```bash
docker compose exec web python manage.py refresh_search_index --full
```

**5. Recompute voting blocs:**

```bash
docker compose exec web python manage.py compute_voting_blocs
```

### Schema-only changes (no data migration)

If you only changed `docker/init/01_schema.sql` (new tables, columns, or enum values) and
the data is already on the VPS, a normal `git pull && docker compose up --build -d` is
sufficient — Django migrations handle schema changes automatically.

Only use the full dump/restore above when you have new bulk data (speeches, votes, etc.)
that was imported locally and needs to be promoted to production.

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
speakers/         Speaker model, profile page, and list view
votes/            Resolution, Vote, CountryVote, and VotingBloc models
  coalitions.py   Named political blocs (COALITIONS list)
  management/     Management commands (compute_voting_blocs)
search/           Full-text search view and materialized view migration
api/              JSON API views and URL routing
debate/           GeneralDebateEntry model
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
| `/speaker/` | Speaker list with name search and country filter |
| `/speaker/<id>/` | Speaker profile |
| `/votes/` | Voting analysis — stats, tools, and recent votes |
| `/votes/blocs/` | Voting blocs — named groups and data-driven clusters |
| `/votes/compare/` | Compare voting records of two countries |
| `/votes/map/` | Interactive world map of voting similarity |
| `/votes/resolutions/` | Browse all resolutions |
| `/votes/bloc/<slug>/` | Individual named bloc detail |
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
| `voting_blocs` | `VotingBloc` | Data-driven clusters (populated by `compute_voting_blocs`) |
| `general_debate_entries` | `GeneralDebateEntry` | General Debate speech entries |

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

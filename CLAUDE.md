# Agent Instructions

This file contains instructions for AI agents working on this codebase.

## Project

A Django web application for exploring United Nations meetings, transcripts, speeches, and votes. See `PLAN.md` for the full specification and `README.md` for user-facing documentation.

## Stack

- Python 3.12, Django 5.2, PostgreSQL 16
- No CSS framework — plain CSS in `static/css/style.css`
- No JavaScript framework — minimal vanilla JS only
- Docker Compose for local and production deployment

## Running the App

```bash
# Local dev (requires PostgreSQL at localhost:5432/unproject)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Docker
docker compose up --build
```

## Verifying Changes

Always run the Django system check and smoke-test key views after making changes:

```bash
python manage.py check
python manage.py shell -c "
from django.test import Client
c = Client()
assert c.get('/', SERVER_NAME='localhost').status_code == 200
assert c.get('/meeting/', SERVER_NAME='localhost').status_code == 200
assert c.get('/search/?q=nuclear', SERVER_NAME='localhost').status_code == 200
assert c.get('/votes/', SERVER_NAME='localhost').status_code == 200
assert c.get('/votes/map/', SERVER_NAME='localhost').status_code == 200
assert c.get('/votes/compare/', SERVER_NAME='localhost').status_code == 200
print('All OK')
"
```

## Project Structure

```
un_site/          Django project config (settings, root urls, wsgi)
core/             Homepage view, base template tags (query_tags.py)
meetings/         Document + DocumentItem models; meeting list/detail views
speeches/         Speech + StageDirection models
countries/        Country model + profile page
speakers/         Speaker model + profile page
votes/            Resolution + Vote + CountryVote models
search/           Full-text search view; materialized view migration
templates/        All HTML templates
static/css/       style.css — the only stylesheet
docker/init/      01_schema.sql — DB init script for Docker
```

## Database Models

All custom models use `managed = False` — their tables are pre-existing in PostgreSQL and Django must never drop or recreate them. Do not change `managed = False` to `True`.

Django's own tables (auth, admin, sessions) are managed normally.

Two search materialized views are created by migrations:
- `speech_search_index` — legacy per-speech index (migration 0001)
- `search_index` — unified index covering speeches and resolutions with weighted tsvectors (migration 0002)

To refresh after a data load, use the management command:

```bash
python manage.py refresh_search_index --full
# or inside Docker:
docker compose exec web python manage.py refresh_search_index --full
```

## Key Conventions

- **Meeting slugs**: `document.symbol` with `/` and `.` replaced by `-`. Example: `A/78/PV.12` → `A-78-PV-12`. The `slug` property lives on `Document`.
- **URL structure**: `/meeting/<slug>/`, `/country/<iso3>/`, `/speaker/<pk>/`, `/search/?q=...`
- **Speech anchors**: `#speech-<id>` on the meeting page. Search results link with `?q=<term>#speech-<id>` so the JS highlighter can mark the term.
- **Agenda item anchors**: `#item-<pk>` injected by the view as `item_header` entries in the transcript list.
- **Pagination**: use the `{% include "partials/pagination.html" with page_obj=page %}` partial. It relies on the `url_with_page` template tag from `core/templatetags/query_tags.py`.

## Updating the Docker Init Schema

When the database schema changes (new tables, new columns, new enum values), regenerate `docker/init/01_schema.sql`:

```bash
pg_dump \
  --schema-only --no-owner --no-privileges \
  --exclude-table=django_migrations \
  --exclude-table=django_admin_log \
  --exclude-table=django_content_type \
  --exclude-table=django_session \
  --exclude-table=auth_group \
  --exclude-table=auth_group_permissions \
  --exclude-table=auth_permission \
  --exclude-table=auth_user \
  --exclude-table=auth_user_groups \
  --exclude-table=auth_user_user_permissions \
  --exclude-table=speech_search_index \
  postgresql://myuser:mypassword@localhost:5432/unproject \
  -f docker/init/01_schema.sql
```

Then `docker compose down -v && docker compose up` to apply to a fresh volume.

## Adding a New App

1. Create the app directory with `__init__.py`, `apps.py`, `models.py`, `views.py`, `urls.py`
2. Add to `INSTALLED_APPS` in `un_site/settings.py`
3. Add an empty migration in `<app>/migrations/0001_initial.py` (models are unmanaged)
4. Include the app's URLs in `un_site/urls.py`

## Style Rules

- Keep JavaScript minimal — no frameworks, no bundlers
- Keep CSS in `static/css/style.css` — no inline `<style>` blocks; page-specific styles may live in `{% block extra_head %}` when tightly scoped to one template
- All templates extend `templates/base.html`
- Use `{% block extra_js %}{% endblock %}` for page-specific scripts
- Run `python manage.py check` before committing
- Exclude sentinel dates (1900-01-01) from all date-sensitive queries using `document__date__year__gt=1900`
- Build JSON API URLs in the view (not in templates) and pass them as context variables to avoid messy template conditionals

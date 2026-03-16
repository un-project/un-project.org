# TODO

Tracked tasks and future features for the UN Project web application.

## In Progress / Near-term

- [x] **Country ISO codes + flags** — 195 UN member states matched; `iso2`/`iso3` populated in DB; SVG flags in `static/flags/<ISO3>.svg`. Script: `scripts/populate_iso_and_flags.py`.
- [x] **Speaker photos** — script `scripts/fetch_speaker_photos.py` downloads from Wikipedia; displayed on speaker page and inline in meeting/country speech lists. Coverage is limited (few matches found); left as-is.
- [ ] **Meetings list — add speech count** — annotate each document with the number of speeches for display on the list page.

## Search

- [x] **Unified search index** — `search_index` materialized view aggregates speeches (speaker A, country B, text C) and resolutions (symbol A, title B, category C) with pre-computed weighted tsvectors and GIN index. `SearchQuery(search_type='websearch')` + `SearchRank(cover_density=True)` used throughout.
- [x] **Search result excerpts with highlighted context** — `SearchHeadline` (`ts_headline`) returns up to 3 matched fragments per result with `<mark>` highlights; resolution titles shown as a distinct result type.
- [x] **Refresh management command** — `manage.py refresh_search_index` (uses `CONCURRENTLY` by default, `--full` for blocking refresh).
- [ ] **Search within a meeting** — add an in-page search box on the meeting detail page.
- [ ] **Auto-refresh materialized view** — schedule `manage.py refresh_search_index` via cron or a post-ingest hook to keep `search_index` current.

## Meeting Transcript

- [ ] **Pagination on long transcripts** — very long meetings (100+ speeches) should paginate or lazy-load to keep initial page weight reasonable.
- [ ] **Per-item permalink** — clicking the agenda item number in the sidebar should copy the anchor URL to clipboard.
- [ ] **Votes inline detail** — expand the vote block to show the full country-by-country vote table (currently only shows totals).

## Country Page

- [x] **Voting analysis charts** — dc.js interactive charts (position pie, year bar, category row, vote table) on each country page and at `/votes/` (dedicated page with country selector, accessible from More menu).
- [x] **Session filter** — filter the country's speech and voting history by GA session; dropdown in the country page preserves pagination.

## Speaker Page

- [ ] **Role / title from data** — the `speakers` table has `role` and `title` columns; populate them and display on the speaker page.

## Navigation & UI

- [x] **Breadcrumbs** — add breadcrumb navigation on meeting, country, and speaker pages.
- [ ] **Mobile nav** — the dropdown menu is hover-only; add a touch-friendly toggle for small screens.
- [ ] **Dark mode** — add a `prefers-color-scheme` media query variant.

## Data & Backend

- [ ] **Security Council transcripts** — the architecture already supports `body='SC'`; load SC meeting data when available.
- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI when data is ready.
- [ ] **Timeline of debates** — visualize when countries spoke on a topic across sessions.

## API

- [x] **JSON API** — read-only `JsonResponse` endpoints at `/api/meetings/`, `/api/meetings/<slug>/`, `/api/resolutions/`, `/api/resolutions/<slug>/`. Filterable by `body`, `session`, `year`; paginated at 50 per page.

## Infrastructure

- [ ] **Production settings** — extract a `un_site/settings_prod.py` with proper `SECURE_*` headers, `CONN_MAX_AGE`, and `STATIC_ROOT` configuration.
- [ ] **Health check endpoint** — add `/health/` returning 200 for load-balancer probes.
- [ ] **Logging** — configure Django logging to write structured logs in production.
- [x] **CI** — GitHub Actions workflow runs pytest (model unit tests + view integration tests) against a PostgreSQL 16 service on every push/PR to main.

## Future / Research

- [ ] **LLM summarization** — integrate Claude API to generate debate summaries per agenda item.
- [x] **Country voting alignment graph** — voting-similarity charts (most/least similar countries) implemented on the votes page in majority mode.
- [ ] **Full data pipeline** — automate ingestion of new UN meeting PDFs into the database.

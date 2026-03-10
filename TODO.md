# TODO

Tracked tasks and future features for the UN Project web application.

## In Progress / Near-term

- [ ] **Country ISO codes** — populate `iso2` / `iso3` columns in the `countries` table so flags display correctly. Flag images go in `static/flags/<ISO3>.svg`.
- [ ] **Speaker photos** — add optional photos to `static/speakers/<id>.jpg`; the speaker page already shows them when present.
- [ ] **Meetings list — add speech count** — annotate each document with the number of speeches for display on the list page.

## Search

- [ ] **Use the materialized view** — `search/models.py` defines `SpeechSearchIndex` mapped to the `speech_search_index` materialized view. Switch `search/views.py` to query it instead of annotating `Speech` objects directly, for better performance at scale.
- [ ] **Search result excerpts with highlighted context** — instead of `speech.excerpt` (first 300 chars), use `ts_headline()` from PostgreSQL to return the matching passage.
- [ ] **Search within a meeting** — add an in-page search box on the meeting detail page.
- [ ] **Auto-refresh materialized view** — add a PostgreSQL trigger or a scheduled management command to keep `speech_search_index` up to date when data changes.

## Meeting Transcript

- [ ] **Pagination on long transcripts** — very long meetings (100+ speeches) should paginate or lazy-load to keep initial page weight reasonable.
- [ ] **Per-item permalink** — clicking the agenda item number in the sidebar should copy the anchor URL to clipboard.
- [ ] **Votes inline detail** — expand the vote block to show the full country-by-country vote table (currently only shows totals).

## Country Page

- [ ] **Voting alignment** — show which countries voted the same way most often (requires aggregation over `country_votes`).
- [ ] **Session filter** — filter the country's speech and voting history by GA session.

## Speaker Page

- [ ] **Role / title from data** — the `speakers` table has `role` and `title` columns; populate them and display on the speaker page.

## Navigation & UI

- [ ] **Breadcrumbs** — add breadcrumb navigation on meeting, country, and speaker pages.
- [ ] **Mobile nav** — the dropdown menu is hover-only; add a touch-friendly toggle for small screens.
- [ ] **Dark mode** — add a `prefers-color-scheme` media query variant.

## Data & Backend

- [ ] **Security Council transcripts** — the architecture already supports `body='SC'`; load SC meeting data when available.
- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI when data is ready.
- [ ] **Timeline of debates** — visualize when countries spoke on a topic across sessions.

## API

- [ ] **JSON API** — expose meetings, speeches, and votes as a read-only REST API (Django REST Framework or simple `JsonResponse` views) to support external tools and the LLM summarization feature.

## Infrastructure

- [ ] **Production settings** — extract a `un_site/settings_prod.py` with proper `SECURE_*` headers, `CONN_MAX_AGE`, and `STATIC_ROOT` configuration.
- [ ] **Health check endpoint** — add `/health/` returning 200 for load-balancer probes.
- [ ] **Logging** — configure Django logging to write structured logs in production.
- [ ] **CI** — add a GitHub Actions workflow that runs `manage.py check` and basic view tests on push.

## Future / Research

- [ ] **LLM summarization** — integrate Claude API to generate debate summaries per agenda item.
- [ ] **Country voting alignment graph** — interactive visualization of voting similarity between countries.
- [ ] **Full data pipeline** — automate ingestion of new UN meeting PDFs into the database.

# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term

- [ ] **Meetings list — speech count** — annotate each document with the number of speeches for display on the list page.
- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate them from the data and display on the speaker page.

## Search

- [ ] **Save/share search URL** — ensure all active filters (body, country, speaker, page) round-trip through the URL so searches are shareable and restorable from the URL.
- [ ] **Search autocomplete** — suggest matching speakers or countries in the global nav search box as the user types.

## Meeting Transcript

- [ ] **Download transcript** — offer a plain-text or CSV export of the full meeting transcript.

## Country Page

- [ ] **Most active speakers** — list the top speakers for the country (by speech count) on the country page.
- [ ] **Top topics** — show the agenda categories a country speaks on most often.

## Speaker Page

- [ ] **Speeches by session** — add a session filter to the speaker page, mirroring the country page.
- [ ] **Co-speakers** — list speakers who appear in the same meetings most frequently.

## Resolution & Votes

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI when data is ready.

## Navigation & UI

- [x] **OpenGraph / meta tags** — add `og:title`, `og:description`, and `og:image` to meeting, country, speaker, and resolution pages for social sharing previews.

## Data & Backend

- [ ] **Security Council transcripts** — the architecture already supports `body='SC'`; load SC meeting data when available.
- [ ] **Full data pipeline** — automate ingestion of new UN meeting PDFs into the database.
- [ ] **Timeline of debates** — visualize when countries spoke on a topic across sessions; useful for tracking evolving positions.
- [ ] **Agenda item pages** — dedicate a page to each recurring agenda item, listing all meetings and countries that discussed it.

## Infrastructure

- [x] **Structured logging** — configure Django logging to write structured JSON logs in production.

## Future / Research

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per agenda item, displayed as a collapsible section on the meeting page.
- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or neutral toward a resolution using the Claude API.
- [ ] **RSS / Atom feed** — publish new meetings and resolutions as a feed so users can subscribe to updates.

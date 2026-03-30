# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate them from the data and display on the speaker page.

## Visualisations

- [ ] **Co-sponsorship network** — network graph of countries that co-sponsor resolutions together.
- [ ] **Voting cohesion heatmap** — countries × countries matrix coloured by agreement rate; complement to the compare page.

## Country & Speaker pages

- [ ] **Speech of the day** — highlight a randomly selected speech excerpt on the homepage.

## Meetings & Agenda

- [ ] **Session overview page** — a single page summarising a GA/SC session: key resolutions, most-active countries, top agenda items.
- [ ] **Agenda item → Topic Timeline link** — on agenda item detail pages, add a link to the Topic Timeline pre-filled with the agenda item title.
- [ ] **Related agenda items** — mark agenda items as related (e.g. successor items that were renamed across sessions).

## Resolution & Votes

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI when data is ready.

## Data & Backend

- [ ] **Full data pipeline** — automate ingestion of new UN meeting PDFs into the database.
- [ ] **Flag unattributed speeches** — identify and surface speeches where the speaker has no linked country.
- [ ] **Detect duplicate speeches** — flag speeches that appear to be duplicates within the same document.

## Future / Research

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per agenda item, displayed as a collapsible section on the meeting page.
- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or neutral toward a resolution using the Claude API.
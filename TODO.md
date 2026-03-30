# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate them from the data and display on the speaker page.

## Resolution & Votes

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI when data is ready.

## Data & Backend

- [ ] **Full data pipeline** — automate ingestion of new UN meeting PDFs into the database.

## Future / Research

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per agenda item, displayed as a collapsible section on the meeting page.
- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or neutral toward a resolution using the Claude API.
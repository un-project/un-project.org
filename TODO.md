# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term (data already in DB)

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate
  them from the data and display on the speaker page.

- [ ] **Most contested resolutions** — surface resolutions with the closest Yes/No split
  (e.g. passed by 1–3 votes) as a list or chart on the votes analysis page.

- [ ] **Country speech statistics** — on the country profile, show total words spoken,
  average speech length, most frequent co-speakers, and trend over sessions.

- [ ] **Session coverage indicator** — on the meeting list and country profile, show a
  small badge or warning when OCR quality is low (`ocr_quality_label` column on
  `documents`) so users know the transcript may have errors.

## Awaiting data / extractor work

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI
  when data is ready.

- [ ] **SC transcript coverage** — Security Council verbatim records are partially extracted;
  complete ingestion and enable the SC body filter site-wide.

## UX & search

- [ ] **Saved searches / bookmarks** — allow users to bookmark a search query or country
  profile URL with a shareable permalink that preserves all filter state.

- [ ] **"On this day" widget** — homepage widget showing UN meetings that happened on
  today's date in past years, linking to their transcripts.

- [ ] **Related resolutions** — on the resolution detail page, suggest thematically similar
  resolutions using the existing `resolution_citations` graph or UNBIS topic codes.

- [ ] **Speaker autocomplete in search** — the speaker dropdown in the search form is a
  plain `<select>`; replace with the existing `data-search-url` live-search widget
  for consistency and usability.

- [ ] **Keyboard shortcuts** — `g h` → home, `g s` → search, `g v` → votes; standard
  GitHub-style single-key navigation.

## Voting analysis

- [ ] **Voting consistency score** — for each country, compute the variance of its ideal
  point over time as a "consistency" metric; display on the country Voting Alignment
  tab alongside the timeline.

- [ ] **P5 alignment matrix** — dedicated page showing pairwise agreement rates among the
  five permanent SC members across all years, as a small annotated heatmap.

- [x] **Voting bloc timeline** — animate or facet the existing blocs page by year so users
  can watch bloc membership shift (e.g. Non-Aligned Movement growth, post-Cold War
  realignment).

- [ ] **Resolution outcome predictor accuracy** — back-test the `/votes/predict/` model by
  comparing its predictions against historical outcomes; display a calibration curve.

## Future / Research

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per
  agenda item, displayed as a collapsible section on the meeting page.

- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or
  neutral toward a resolution using the Claude API.

- [ ] **Topic modelling** — run BERTopic or LDA over speech text; surface dominant topics
  per session and per country, linkable from the country and meeting pages.


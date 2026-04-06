# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term (data already in DB)

- [x] **Ambassador / Representative profiles** — `sc_representatives` (5 048 rows, 136 countries)
  displayed in the Representatives tab on country pages. Table shows name, role/notes, SC speech
  year range, speaker page link, and UNDL record link. Paginated (30 per page).

- [x] **Ideal point chart on country pages** — line chart with ±1 SE confidence band
  rendered in the Voting Analysis tab. Keyed by iso3 from `country_ideal_points`
  (201 countries, 1946–2025). Zero line marks USA reference position.

- [x] **Resolution full text** — collapsible `<details>` section on the resolution detail page.
  SC resolutions labelled "CR-UNSC"; GA resolutions note OCR extraction. Scrollable at 600px max.

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate
  them from the data and display on the speaker page.

## Awaiting data / extractor work

- [x] **General Debate speech page** — detail page at `/debate/<session>/<pk>/` with full
  text, speaker/country/meeting metadata, prev/next navigation. Session list and country
  page General Debate tab now link to each entry. Shows a placeholder when text is NULL
  (re-run `import_gdebate_corpus.py` with `DATABASE_URL=postgresql://myuser:mypassword@localhost:5433/unproject`).

- [x] **UNBIS subject taxonomy on resolutions** — `resolutions.category` already holds UNBIS scheme
  names (18 values, 6 109 rows). Category filter added to the resolution list sidebar; category
  displayed as a linked tag badge on resolution cards and the resolution detail page.

- [ ] **Co-sponsorship list on resolution pages** — depends on extracting co-sponsor lines from
  speeches or importing UNBench draft JSONs. Once a `resolution_sponsors` table exists, show
  the sponsoring countries on the resolution detail page and add co-sponsorship to country profiles.

- [ ] **Alignment time series between two countries** — requires computing a
  `country_alignment_series (country_id_a, country_id_b, year, agreement_rate)` table in the
  extractor. Once available, add a chart to the compare page showing how voting agreement between
  two countries has evolved year by year, with inflection-point annotations.

## Visualisations

- [x] **Ideal point global timeline** — D3 heatmap at `/votes/ideal-points/`: countries × years,
  red (opposing) → white (neutral) → blue (Western) color scale; sorted by mean ideal point;
  1991 and 2022 era markers; hover tooltip; linked from the votes index.

- [ ] **Co-sponsorship network** — network graph of countries that co-sponsor resolutions
  together. Requires `resolution_sponsors` table (extractor work).

- [x] **Voting cohesion heatmap** — D3 SVG at `/votes/cohesion/`: top 60 most active countries,
  pairwise agreement rates via SQL self-join, sorted by ideal point, grey→green color scale;
  click any cell to open the compare page for those two countries.

## Country & Speaker pages

- [x] **Speech of the day** — homepage shows a daily speech excerpt (deterministic seed from
  date ordinal, speeches ≥500 chars), with speaker, country flag, meeting link, and "Read full
  speech" link. Changes automatically each day; no caching or extra DB columns needed.

## Meetings & Agenda

- [ ] **Session overview page** — a single page summarising a GA/SC session: key resolutions,
  most-active countries, top agenda items.

- [x] **Agenda item → Topic Timeline link** — "Topic Timeline →" link added to the agenda item
  detail page subtitle, pre-filled with the item title via `?q={{ title|urlencode }}`.

- [ ] **Related agenda items** — mark agenda items as related (e.g. successor items that were
  renamed across sessions).

## Resolution & Votes

- [x] **P5 veto tracking** — `/votes/vetoes/`: 271 vetoes from DPPA dataset with stacked bar
  timeline (D3), per-P5 stat cards, filterable table by vetoing country, and links to meeting
  documents where matched. `Veto` and `VetoCountry` models added to the votes app.

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI
  when data is ready.

## Data & Backend

- [ ] **Full data pipeline** — automate ingestion of new UN meeting PDFs into the database.

- [ ] **Flag unattributed speeches** — identify and surface speeches where the speaker has
  no linked country.

- [ ] **Detect duplicate speeches** — flag speeches that appear to be duplicates within the
  same document.

## Future / Research

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per
  agenda item, displayed as a collapsible section on the meeting page.

- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or
  neutral toward a resolution using the Claude API.

- [ ] **Explanation-of-vote tagging** — tag speeches given immediately before/after a vote as
  `explanation_of_vote` (requires extractor work). Surface them as a dedicated section on the
  resolution detail page — the most policy-relevant content around any vote.

- [ ] **Data-driven bloc detection** — apply clustering to the pairwise voting-agreement matrix
  per year to recover blocs automatically, replacing the hardcoded `coalitions.py` list. Store
  in a `voting_blocs (country_id, year, bloc)` table with rolling 5-year windows.

- [ ] **Vote prediction model** — predict a country's vote given its ideal point, resolution
  category, and sponsoring region. Useful for flagging anomalous votes.

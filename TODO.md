# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term (data already in DB)

- [ ] **Ambassador / Representative profiles** — `permanent_representatives` (2 821 rows) and
  `sc_representatives` are populated. The "Representatives" tab header already appears on country
  pages but renders no content. Render the list with name, salutation, dates, and UNDL link.

- [ ] **Ideal point chart on country pages** — `country_ideal_points` holds 11 608 rows
  (1946–2025): `(country_id, year, ideal_point, se)`. Add a sparkline or small line chart on
  the country profile showing how the country's UN voting alignment has shifted over time.
  Positive = more aligned with USA (Bailey–Strezhnev–Voeten 2PL IRT model).

- [ ] **Resolution full text** — 6 465 SC resolutions already have `full_text` populated via
  CR-UNSC. Display it in a collapsible section on the resolution detail page.

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate
  them from the data and display on the speaker page.

## Awaiting data / extractor work

- [ ] **General Debate speech page** — `general_debate_entries.text` column exists but is empty
  (the Baturo corpus import has not been run yet). Once populated, add a detail page per speech
  showing the full text, with links from the session and country pages.

- [ ] **UNBIS subject taxonomy on resolutions** — the extractor normalises subjects to 18 UNBIS
  scheme names (`resolutions.subjects` column, not yet added to the DB schema). Once the column
  exists, display subjects as tags on the resolution detail page and add a subject filter to the
  resolution list and country vote pages. Also requires migrating the existing `category` field
  from the old 12-category scheme.

- [ ] **Co-sponsorship list on resolution pages** — depends on extracting co-sponsor lines from
  speeches or importing UNBench draft JSONs. Once a `resolution_sponsors` table exists, show
  the sponsoring countries on the resolution detail page and add co-sponsorship to country profiles.

- [ ] **Alignment time series between two countries** — requires computing a
  `country_alignment_series (country_id_a, country_id_b, year, agreement_rate)` table in the
  extractor. Once available, add a chart to the compare page showing how voting agreement between
  two countries has evolved year by year, with inflection-point annotations.

## Visualisations

- [ ] **Ideal point global timeline** — a heatmap or animated chart of all countries' ideal
  points over time, revealing geopolitical blocs and their evolution (Cold War → post-1991 →
  post-2022). Depends on the `country_ideal_points` table (already populated).

- [ ] **Co-sponsorship network** — network graph of countries that co-sponsor resolutions
  together. Requires `resolution_sponsors` table (extractor work).

- [ ] **Voting cohesion heatmap** — countries × countries matrix coloured by agreement rate;
  complement to the compare page.

## Country & Speaker pages

- [ ] **Speech of the day** — highlight a randomly selected speech excerpt on the homepage.

## Meetings & Agenda

- [ ] **Session overview page** — a single page summarising a GA/SC session: key resolutions,
  most-active countries, top agenda items.

- [ ] **Agenda item → Topic Timeline link** — on agenda item detail pages, add a link to the
  Topic Timeline pre-filled with the agenda item title.

- [ ] **Related agenda items** — mark agenda items as related (e.g. successor items that were
  renamed across sessions).

## Resolution & Votes

- [ ] **P5 veto tracking** — SC vetoed draft resolutions are absent from the UNDL CSV but
  documented in the UN Journal and Security Council Report. Import veto data to complete the
  SC picture and enable veto-pattern analysis.

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

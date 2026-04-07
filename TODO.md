# TODO

Tracked tasks and future features for the UN Project web application.

## Near-term (data already in DB)

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate
  them from the data and display on the speaker page.

- [x] **Voeten `important_vote` filter** — the `resolutions` table now has an `important_vote`
  boolean (US State Dept classification). Add it as a checkbox filter on the resolution list
  page and as a toggle on the country voting analysis page. Add the field to the `Resolution`
  model in `votes/models.py`.

- [x] **Voeten issue-code tags** — the `resolutions` table has six boolean columns:
  `issue_me` (Middle East), `issue_nu` (Nuclear/arms), `issue_co` (Colonialism),
  `issue_hr` (Human rights), `issue_ec` (Economic), `issue_di` (Disarmament/Cold War).
  Surface them as filter tags on the resolution list (alongside the UNBIS category), on
  resolution detail pages, and as a breakdown axis on the country voting and compare pages.

- [x] **Issue-code breakdown on compare page** — show the two-country voting agreement
  disaggregated by Voeten issue code (ME / NU / CO / HR / EC / DI) as a small bar chart
  or table below the year-trend chart.

## Awaiting data / extractor work

- [ ] **Co-sponsorship list on resolution pages** — depends on extracting co-sponsor lines from
  speeches or importing UNBench draft JSONs. Once a `resolution_sponsors` table exists, show
  the sponsoring countries on the resolution detail page and add co-sponsorship to country profiles.

- [ ] **Co-sponsorship network** — network graph of countries that co-sponsor resolutions
  together. Requires `resolution_sponsors` table (extractor work).

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI
  when data is ready.

## Meetings & Agenda

- [ ] **Session overview page** — a single page summarising a GA/SC session: key resolutions,
  most-active countries, top agenda items.

- [ ] **Related agenda items** — mark agenda items as related (e.g. successor items that were
  renamed across sessions).

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

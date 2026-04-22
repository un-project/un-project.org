# TODO

Tracked tasks and future features for the UN Project web application.

## Issues

- [ ] **Similarity map / historical states** — the similarity map must show the historical
  states as they existed during their respective era
  
- [ ] **Fix speaker photos** — The `fetch_speaker_photos.py` script is unusable because it
  retrieves photos of a different person rather than the UN speaker.

## Near-term (data already in DB)

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate
  them from the data and display on the speaker page.

## Awaiting data / extractor work

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI
  when data is ready.

## Meetings & Agenda

- [ ] **Session overview page** — a single page summarising a GA/SC session: key resolutions,
  most-active countries, top agenda items.

- [ ] **Related agenda items** — mark agenda items as related (e.g. successor items that were
  renamed across sessions).

## Quick wins (data already in DB)

- [ ] **Key votes page** — list resolutions with the closest margins (≤ 5 vote difference) or
  where P5 members split. Purely SQL over existing `country_votes` data. High research value.

- [ ] **Ideal point timeline** — `country_ideal_points` is populated; add a small line chart on
  the country page showing the country's IRT ideal point moving left/right over decades.

- [ ] **"This meeting at a glance"** — collapsible summary on meeting detail: N speeches,
  N countries represented, resolutions adopted, adjournment time from stage directions.

## Medium effort

- [ ] **"Similar countries" on country page** — top-5 most/least aligned countries from the
  precomputed alignment series, linking to the compare page. Data already computed.

- [ ] **Resolution search filters** — the main `/search/` page still lacks a resolution-only
  mode and date-range filter (resolution list sidebar already has text search).

## Future / Research

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per
  agenda item, displayed as a collapsible section on the meeting page.

- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or
  neutral toward a resolution using the Claude API.

- [ ] **Explanation-of-vote tagging** — tag speeches given immediately before/after a vote as
  `explanation_of_vote` (requires extractor work). Surface them as a dedicated section on the
  resolution detail page — the most policy-relevant content around any vote.

- [ ] **Vote prediction model** — predict a country's vote given its ideal point, resolution
  category, and sponsoring region. Useful for flagging anomalous votes.

# TODO

Tracked tasks and future features for the UN Project web application.

## Issues

- [ ] **Voting similarity map bug** — intermittent "Not enough shared votes" even though data
  exists; the query was rewritten to SQL + cached so this should be much rarer, but monitor.

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

- [ ] **Country speech frequency chart** — bar chart of speeches per session/year on the
  country profile page, alongside the existing voting tab. Data already in `speeches`.

- [ ] **General Debate word cloud per country** — word cloud of a country's General Debate
  speeches over the years, drawn from `general_debate_entries`. Makes country pages richer.

- [ ] **Ideal point timeline** — `country_ideal_points` is populated; add a small line chart on
  the country page showing the country's IRT ideal point moving left/right over decades.

- [ ] **P5 voting breakdown on resolution cards/detail** — show 🇺🇸🇬🇧🇫🇷🇷🇺🇨🇳 vote icons
  inline on resolution list cards and the detail page. One extra query, high signal.

- [ ] **"This meeting at a glance"** — collapsible summary on meeting detail: N speeches,
  N countries represented, resolutions adopted, adjournment time from stage directions.

## Medium effort

- [ ] **"Similar countries" on country page** — top-5 most/least aligned countries from the
  precomputed alignment series, linking to the compare page. Data already computed.

- [x] **Resolution search filters** — text search by title/symbol added to the resolution list
  sidebar; the main `/search/` page still lacks a resolution-only mode and date-range filter.

- [ ] **Speaker search / list** — a `/speaker/` list page with name autocomplete so speakers
  can be found without browsing through country pages.

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

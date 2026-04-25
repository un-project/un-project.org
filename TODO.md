# TODO

Tracked tasks and future features for the UN Project web application.

## Issues

- [x] **Similarity map / historical states** — the similarity map must show the historical
  states as they existed during their respective era
  
- [x] **Fix speaker photos** — The `fetch_speaker_photos.py` script is unusable because it
  retrieves photos of a different person rather than the UN speaker.

## Near-term (data already in DB)

- [ ] **Speaker role / title** — the `speakers` table has `role` and `title` columns; populate
  them from the data and display on the speaker page.

## Awaiting data / extractor work

- [ ] **Amendment tracking** — the `amendments` table is reserved; implement models and UI
  when data is ready.

## Meetings & Agenda

- [x] **Session overview page** — a single page summarising a GA/SC session: key resolutions,
  most-active countries, top agenda items.

- [ ] **Related agenda items** — mark agenda items as related (e.g. successor items that were
  renamed across sessions).

## Quick wins (data already in DB)

- [ ] **Key votes page** — list resolutions with the closest margins (≤ 5 vote difference) or
  where P5 members split. Purely SQL over existing `country_votes` data. High research value.

- [x] **Ideal point timeline on country page** — `country_ideal_points` is populated; add a
  line chart with SE confidence band on each country profile page showing its ideal point from
  1946 to today. The `bsv2017_mcmc` values match Voeten's scale (mean=0, std=1) so they're
  directly comparable to published political science literature.

- [x] **"Closest neighbours" widget** — for any country in any year, query
  `country_ideal_points` for the N countries with the smallest `|ip - X|`. Shows which
  countries were most aligned in a given GA session. Cheap to compute at request time; could
  live on the country profile page or the compare page.

- [x] **P5 divergence chart** — dedicated chart showing USA/UK/France vs Russia/China ideal
  points drifting apart over time. Good homepage or "About the data" visual that immediately
  explains the site's value proposition.

- [ ] **"This meeting at a glance"** — collapsible summary on meeting detail: N speeches,
  N countries represented, resolutions adopted, adjournment time from stage directions.

## Medium effort

- [ ] **Canonical ideal point source** — `country_ideal_points` now has three sources
  (`bsv2017_mcmc`, `voeten_bsv2017`, `computed_irt`). The site should expose only one series
  per country per year. Options: materialise a view with precedence
  `bsv2017_mcmc > voeten_bsv2017 > computed_irt`, or add an `is_canonical BOOLEAN` column
  populated by the extractor. Required before mixing sources in any chart.

- [ ] **Anomalous vote flagging** — for each recorded vote, compare the country's actual
  position to what its ideal point predicts. A high-IP country voting Yes on a resolution the
  USA voted No on is a detectable anomaly. Flag these on resolution pages as "surprising vote".

- [ ] **Bloc visualisation per year** — group countries by ideal point quartile per session,
  overlay on a world map. Shows the Western bloc vs. G77/non-aligned movement shifting over
  time. Depends on canonical ideal point source.

- [x] **Issue-area ideal points** — the `important_vote`, `issue_me`, `issue_nu`, `issue_hr`
  columns on resolutions allow computing ideal points conditional on issue area. Separate
  timelines for "how aligned is country X on human rights votes" vs "disarmament votes" —
  much richer than a single dimension. Requires extractor work (filtered CSV per issue area).
  *Implemented as per-issue-area yes-rate (5yr rolling avg) on country pages — full IRT
  per issue area can replace this once extractor work is done.*

- [x] **"Similar countries" on country page** — top-5 most/least aligned countries from the
  precomputed alignment series, linking to the compare page. Data already computed.

- [x] **Resolution search filters** — the main `/search/` page still lacks a resolution-only
  mode and date-range filter (resolution list sidebar already has text search).

## Future / Research

- [x] **Vote prediction** — given a new resolution and its sponsoring bloc, predict each
  country's vote from its current ideal point. Useful as a "before the vote" feature during
  live GA sessions.

- [ ] **LLM summarization** — use the Claude API to generate concise debate summaries per
  agenda item, displayed as a collapsible section on the meeting page.

- [ ] **Sentiment / position analysis** — classify speeches as supportive, critical, or
  neutral toward a resolution using the Claude API.

- [ ] **Explanation-of-vote tagging** — tag speeches given immediately before/after a vote as
  `explanation_of_vote` (requires extractor work). Surface them as a dedicated section on the
  resolution detail page — the most policy-relevant content around any vote.

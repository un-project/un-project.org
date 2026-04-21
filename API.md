# UN Project — API Reference

The UN Project exposes a read-only JSON API for accessing meeting, speaker, resolution, and country data.

**Base URL:** `https://un-project.org/api/`

All endpoints return JSON. Paginated endpoints include `count`, `next`, `previous`, and `results` fields.

---

## Countries

### List countries
```
GET /api/countries/
```
Returns all countries, ordered by name (paginated, 50 per page).

| Parameter | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `q`       | string | Filter by name fragment              |
| `page`    | int    | Page number                          |

**Response fields:** `id`, `name`, `short_name`, `iso2`, `iso3`, `un_member_since`, `flag_url`, `url`

---

### Get a country
```
GET /api/countries/<iso3>/
```

---

### Country ideal points
```
GET /api/countries/<iso3>/ideal-points/
```
Returns the IRT ideal point time series for a country (Voeten dataset).

**Response:** `iso3`, `data` (array of `{ year, ideal_point, se }`)

---

### Country voting alignment
```
GET /api/countries/<iso3>/alignment/
```
Returns voting alignment data. Requires one of:

| Parameter | Type   | Description                                              |
|-----------|--------|----------------------------------------------------------|
| `partner` | string | ISO3 code — returns pairwise agreement rate over time    |
| `year`    | int    | Returns top 50 partners by agreement rate for that year  |

**Response (`?partner=`):** `country`, `partner`, `data` (array of `{ year, agreement_rate, n_votes }`)

**Response (`?year=`):** `country`, `year`, `data` (array of `{ partner, partner_name, agreement_rate, n_votes }`, min 5 shared votes)

---

### Country speeches
```
GET /api/countries/<iso3>/speeches/
```

| Parameter  | Type   | Description          |
|------------|--------|----------------------|
| `body`     | string | `GA` or `SC`         |
| `year_from`| int    | Start year           |
| `year_to`  | int    | End year             |
| `page`     | int    | Page number          |

**Response fields:** `url`, `speaker_name`, `speaker_url`, `speaker_pk`, `document_symbol`, `document_url`, `date`, `body`, `excerpt`

---

### Country representatives
```
GET /api/countries/<iso3>/representatives/
```
Lists all speakers who have spoken on behalf of this country, with year ranges.

**Response fields:** `name`, `url`, `role`, `first_year`, `last_year`

---

### Country SC representatives
```
GET /api/countries/<iso3>/sc-reps/
```
Official Security Council representatives from the UNDL.

**Response fields:** `name`, `salutation`, `sc_president`, `notes`, `undl_link`, `speaker_url`, `first_year`, `last_year`

---

## Speakers

### List speakers
```
GET /api/speakers/
```
Returns all speakers, ordered by name (paginated, 50 per page).

| Parameter | Type   | Description                              |
|-----------|--------|------------------------------------------|
| `country` | string | Filter by ISO3 code (e.g. `FRA`) or numeric country ID |
| `page`    | int    | Page number                              |

**Response fields:** `id`, `name`, `country`, `country_iso3`, `organization`, `role`, `title`, `url`

---

### Get a speaker
```
GET /api/speakers/<id>/
```

---

### Search speakers (autocomplete)
```
GET /api/speakers/search/?q=<query>
```
Returns up to 30 matching speakers. Minimum 2 characters required.

**Response fields:** `id`, `name`, `detail` (country or organization), `country_iso3`

---

### Speaker speeches
```
GET /api/speakers/<id>/speeches/
```

| Parameter  | Type   | Description  |
|------------|--------|--------------|
| `body`     | string | `GA` or `SC` |
| `year_from`| int    | Start year   |
| `year_to`  | int    | End year     |
| `page`     | int    | Page number  |

**Response fields:** `url`, `document_symbol`, `document_url`, `date`, `body`, `excerpt`

---

### Speaker meetings
```
GET /api/speakers/<id>/meetings/
```
Lists all meetings in which a speaker appeared.

Same filter parameters as speaker speeches. Response fields match the meeting list.

---

## Meetings

### List meetings
```
GET /api/meetings/
```
Returns all meetings, paginated (50 per page).

| Parameter | Type   | Description                  |
|-----------|--------|------------------------------|
| `body`    | string | `GA` or `SC`                 |
| `session` | int    | GA session number            |
| `year`    | int    | Calendar year of the meeting |
| `page`    | int    | Page number                  |

**Response fields:** `symbol`, `body`, `session`, `meeting_number`, `date`, `location`, `url`, `docs_un_url`

---

### Get a meeting (with speeches)
```
GET /api/meetings/<slug>/
```
The slug is the document symbol with `/` and `.` replaced by `-` (e.g. `A/78/PV.12` → `A-78-PV-12`).

Includes all fields from the list endpoint plus a `speeches` array:

| Field          | Description                              |
|----------------|------------------------------------------|
| `id`           | Speech ID                                |
| `speaker`      | Speaker name                             |
| `country`      | Country display name                     |
| `country_iso3` | ISO 3166-1 alpha-3 code                  |
| `organization` | Organization name (if not a country rep) |
| `language`     | Language code                            |
| `on_behalf_of` | Delegation name if acting on behalf of   |
| `unattributed` | `true` if the speaker has no country or organization linked |
| `duplicate`    | `true` if this speech appears to be a duplicate within the meeting |
| `text`         | Full speech text                         |

---

## Resolutions

### List resolutions
```
GET /api/resolutions/
```
Returns all resolutions, ordered by session (paginated, 50 per page).

| Parameter      | Type    | Description                                       |
|----------------|---------|---------------------------------------------------|
| `body`         | string  | `GA` or `SC`                                      |
| `session`      | int     | Session number                                    |
| `category`     | string  | Exact match on resolution category                |
| `important_vote` | bool  | `true` to return only Voeten-coded important votes |
| `issue`        | string  | Voeten issue code: `me`, `nu`, `co`, `hr`, `ec`, `di` |
| `sponsor`      | string  | ISO3 code — filter to resolutions sponsored by this country |
| `page`         | int     | Page number                                       |

**Response fields:** `id`, `draft_symbol`, `adopted_symbol`, `body`, `session`, `title`, `category`, `important_vote`, `issue_codes`, `url`, `docs_un_url`, `votes` (array)

**Issue codes:** `me` = Middle East, `nu` = Nuclear/Arms, `co` = Colonialism, `hr` = Human Rights, `ec` = Economic Development, `di` = Disarmament/Cold War

---

### Get a resolution (with vote breakdown)
```
GET /api/resolutions/<slug>/
```
The slug follows the same convention as meetings.

Includes all list fields plus `draft_text`, `sponsors` (array), and a full `country_votes` array in each vote record:

| Field      | Description               |
|------------|---------------------------|
| `country`  | Country display name      |
| `iso3`     | ISO 3166-1 alpha-3 code   |
| `position` | `yes`, `no`, `abstain`, or `absent` |

**Sponsors:** array of `{ country_name, iso3, url }` (ISO3 and URL are `null` for unmatched entries)

---

### Resolution citations
```
GET /api/resolutions/<slug>/citations/
```
Returns a depth-1 citation neighbourhood as nodes and directed edges for graph rendering.

**Response:** `nodes` (array of `{ id, symbol, title, url, is_center }`), `edges` (array of `{ source, target, weight }`)

---

### Resolution sponsors
```
GET /api/resolutions/<slug>/sponsors/
```

**Response:** `resolution`, `sponsors` (array of `{ country_name, iso3, url }`)

---

## Vetoes

### List vetoes
```
GET /api/vetoes/
```
Returns all Security Council vetoes (paginated, 50 per page).

| Parameter | Type   | Description                              |
|-----------|--------|------------------------------------------|
| `country` | string | ISO3 code — filter to vetoes cast by this country |
| `year`    | int    | Filter by year                           |
| `page`    | int    | Page number                              |

**Response fields:** `dppa_id`, `draft_symbol`, `date`, `meeting_symbol`, `agenda`, `short_agenda`, `n_vetoing_pm`, `vetoing_countries` (array of `{ name, iso3 }`), `dppa_url`

---

## Word Cloud

### Country word cloud
```
GET /api/wordcloud/
```
Returns the top keywords for a country, suitable for rendering a word cloud.

| Parameter    | Type   | Description                                                              |
|--------------|--------|--------------------------------------------------------------------------|
| `country_id` | int    | Country primary key (required)                                           |
| `source`     | string | `speeches` (default) or `debate` (General Debate entries only)           |
| `body`       | string | `GA` or `SC` — filters source speeches (ignored for `source=debate`)     |
| `session`    | int    | Session number — filters source speeches                                 |

**Response:** `words` (array of `{ text, weight }`, up to 150 words)

---

## Search

### Full-text search
```
GET /api/search/?q=<query>
```
Searches speeches and resolutions using PostgreSQL full-text search. Minimum 2 characters required.

| Parameter | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `q`       | string | Search query (websearch syntax)      |
| `body`    | string | `GA` or `SC`                         |
| `type`    | string | `speech` or `resolution`             |
| `page`    | int    | Page number                          |

**Response fields:** `item_type`, `item_id`, `document_symbol`, `date`, `body`, `session`, `speaker_name`, `country_name`, `country_iso3`, `excerpt` (first 300 chars), `url`

Results are ordered by relevance (cover-density rank).

---

## Voting Blocs

### List available years
```
GET /api/voting-blocs/
```
Returns the list of years for which data-driven voting clusters have been computed.

**Response:** `years` (array of integers, sorted descending)

---

### Get clusters for a year
```
GET /api/voting-blocs/?year=<year>
```

| Parameter | Type | Description           |
|-----------|------|-----------------------|
| `year`    | int  | Year to retrieve      |

**Response fields:** `year`, `window` (e.g. `"2018–2022"`), `blocs` (array)

Each bloc in `blocs`:

| Field       | Description                                                        |
|-------------|--------------------------------------------------------------------|
| `index`     | Zero-based cluster index                                           |
| `size`      | Number of member countries                                         |
| `countries` | Array of `{ name, iso3 }`                                          |
| `top_match` | Closest named political group: `{ name, slug, pct }` or `null`    |

---

## Voting data (country-specific)

### Country votes
```
GET /votes/api/<iso3>/
```
Returns all recorded votes for a country.

| Parameter | Type   | Description                       |
|-----------|--------|-----------------------------------|
| `session` | int    | Filter by GA/SC session number    |
| `body`    | string | `GA` or `SC`                      |

**Response fields:** `country`, `iso3`, `votes` (array with `position`, `year`, `date`, `session`, `category`, `resolution`, `title`, `yes_count`, `no_count`, `abstain_count`, `document`, `document_url`, `resolution_url`)

---

### Country voting similarity
```
GET /votes/api/<iso3>/similarity/
```
Returns the 10 most and 10 least similar countries by voting pattern (minimum 10 shared votes).

| Parameter | Type   | Description                                                    |
|-----------|--------|----------------------------------------------------------------|
| `all`     | any    | If present, return all countries sorted by score descending    |

**Response (default):** `similar`, `dissimilar` — each an array of `{ iso3, name, score, shared }`

**Response (`?all=1`):** `countries` — full ranked array of `{ iso3, name, score, shared }`

---

## Rate limiting

API endpoints are rate-limited to **60 requests per minute** per IP address. Responses exceeding the limit return HTTP 429.

---

## Notes

- All data is read-only; no authentication is required.
- Dates are ISO 8601 strings (`YYYY-MM-DD`) or `null`.
- Country ISO codes follow ISO 3166-1 alpha-3. Not all countries have codes assigned (historical delegations may lack them).
- The API is provided for research and non-commercial use.

# UN Project — API Reference

The UN Project exposes a read-only JSON API for accessing meeting, speaker, and resolution data.

**Base URL:** `https://un-project.org/api/`

All endpoints return JSON. Paginated endpoints include `count`, `next`, `previous`, and `results` fields.

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
| `text`         | Full speech text                         |

---

## Resolutions

### List resolutions
```
GET /api/resolutions/
```
Returns all resolutions, ordered by session (paginated, 50 per page).

| Parameter | Type   | Description       |
|-----------|--------|-------------------|
| `body`    | string | `GA` or `SC`      |
| `session` | int    | Session number    |
| `page`    | int    | Page number       |

**Response fields:** `id`, `draft_symbol`, `adopted_symbol`, `body`, `session`, `title`, `category`, `url`, `docs_un_url`, `votes` (array)

---

### Get a resolution (with vote breakdown)
```
GET /api/resolutions/<slug>/
```
The slug follows the same convention as meetings.

Includes all list fields plus a full `country_votes` array in each vote record:

| Field      | Description               |
|------------|---------------------------|
| `country`  | Country display name      |
| `iso3`     | ISO 3166-1 alpha-3 code   |
| `position` | `yes`, `no`, `abstain`, or `absent` |

---

## Voting data (country-specific)

### Country votes
```
GET /votes/api/<iso3>/
```
Returns all recorded votes for a country.

| Parameter | Type | Description           |
|-----------|------|-----------------------|
| `session` | int  | Filter by GA session  |

**Response fields:** `country`, `iso3`, `votes` (array with `position`, `year`, `date`, `session`, `category`, `resolution`, `title`, `yes_count`, `no_count`, `abstain_count`, `document`, `document_url`)

---

### Country voting similarity
```
GET /votes/api/<iso3>/similarity/
```
Returns the 10 most and 10 least similar countries by voting pattern (minimum 10 shared votes).

**Response fields:** `similar`, `dissimilar` — each an array of `{ iso3, name, score, shared }` where `score` is 0–1 (1 = identical voting record).

---

## Rate limiting

API endpoints are rate-limited to **60 requests per minute** per IP address. Responses exceeding the limit return HTTP 429.

---

## Notes

- All data is read-only; no authentication is required.
- Dates are ISO 8601 strings (`YYYY-MM-DD`) or `null`.
- Country ISO codes follow ISO 3166-1 alpha-3. Not all countries have codes assigned (historical delegations may lack them).
- The API is provided for research and non-commercial use.

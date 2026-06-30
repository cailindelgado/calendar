# Missionary Meal Roster Calendar

A Flask REST API for scheduling meals for church missionaries. Members of the church sign up to host a meal for a group of missionaries (elders or sisters) on a given date and time.

## Stack

- Python 3.11+
- Flask + Flask-SQLAlchemy
- SQLite (`instance/db.sqlite`)

## Setup

```bash
uv sync
```

## Running

```bash
uv run flask --app timetable run

# With hot reload
uv run flask --app timetable run --debug
```

## Tests

```bash
uv run pytest
```

## API

All endpoints are mounted at `/calendar`.

### `GET /calendar/health`

Returns `{"status": "ok"}`.

---

### `GET /calendar/events`

Returns all events. Optionally filter by missionary type:

```
GET /calendar/events?type=elders
GET /calendar/events?type=sisters
```

**Response** `200`
```json
[
  {
    "id": 1,
    "person_id": 1,
    "f_name": "Jane",
    "l_name": "Smith",
    "phone_num": "0400 000 000",
    "description": "Bring lasagne",
    "time": "2099-01-01T12:00:00",
    "missionary_type": "elders"
  }
]
```

---

### `GET /calendar/events/<id>`

**Response** `200` — same shape as a single item above.  
**Response** `404` — `{"error": "Event not found"}`

---

### `POST /calendar/events`

Create an event. Returns a `fingerprint` token that is required to modify or delete the event later — **store it, it is only shown once**.

If a person with the same `phone_num` + `l_name` already exists they are reused; otherwise a new person record is created.

Phone numbers are normalised to E.164 format. Numbers without a country code default to Australia (+61).

**Request body**
```json
{
  "phone_num": "0400000000",
  "f_name": "Jane",
  "l_name": "Smith",
  "time": "2099-01-01T12:00:00",
  "missionary_type": "elders",
  "description": "Bring lasagne"
}
```

| Field | Required | Notes |
|---|---|---|
| `phone_num` | yes | Any parseable format |
| `f_name` | yes | |
| `l_name` | yes | |
| `time` | yes | ISO 8601, must be in the future |
| `missionary_type` | yes | `"elders"` or `"sisters"` |
| `description` | no | Max 200 characters |

**Response** `201`
```json
{
  "id": 1,
  "fingerprint": "<hex-token>",
  ...
}
```

---

### `PUT /calendar/events/<id>`

Update an event. Requires the `X-Fingerprint-ID` header set to the token returned when the event was created.

**Request headers**
```
X-Fingerprint-ID: <hex-token>
```

**Request body** — same fields as POST (all optional except `time`).

**Response** `200` — updated event.  
**Response** `403` — wrong fingerprint.  
**Response** `404` — event not found.

---

### `DELETE /calendar/events/<id>`

Delete an event. Requires the `X-Fingerprint-ID` header.

**Request headers**
```
X-Fingerprint-ID: <hex-token>
```

**Response** `200` — deleted event.  
**Response** `403` — wrong fingerprint.  
**Response** `404` — event not found.

## Authorization

Mutating operations (PUT, DELETE) are protected by a fingerprint token. When you POST to create an event, the server generates a random hex token and returns it in the `fingerprint` field of the response. Pass this as the `X-Fingerprint-ID` header to authorize future edits or deletion of that event.

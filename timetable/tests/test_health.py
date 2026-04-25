from .helpers import post_event, FINGERPRINT, OTHER_FINGERPRINT


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get('/calendar/health')
    assert r.status_code == 200
    assert r.get_json()['status'] == 'ok'


# ---------------------------------------------------------------------------
# GET /events
# ---------------------------------------------------------------------------

def test_get_events_empty(client):
    r = client.get('/calendar/events')
    assert r.status_code == 200
    assert r.get_json() == []


def test_get_events_returns_created(client):
    post_event(client)
    r = client.get('/calendar/events')
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_get_event_by_id(client):
    created = post_event(client).get_json()
    r = client.get(f'/calendar/events/{created["id"]}')
    assert r.status_code == 200
    assert r.get_json()['id'] == created['id']


def test_get_event_not_found(client):
    r = client.get('/calendar/events/999')
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /events
# ---------------------------------------------------------------------------

def test_post_event_success(client):
    r = post_event(client)
    assert r.status_code == 201
    data = r.get_json()
    assert 'id' in data


def test_post_event_past_time_rejected(client):
    r = post_event(client, time='2000-01-01T00:00:00')
    assert r.status_code == 400


def test_post_event_with_description(client):
    r = post_event(client, description='Bring lasagne')
    assert r.status_code == 201
    assert r.get_json()['description'] == 'Bring lasagne'


def test_post_event_missing_required_field(client):
    """POST without a required field should return 400, not 500."""
    r = client.post(
        '/calendar/events',
        json={'f_name': 'Jane', 'time': '2099-06-01T12:00:00'},
        headers={'X-Fingerprint-ID': FINGERPRINT},
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /events
# ---------------------------------------------------------------------------

def test_delete_event_success(client):
    event_id = post_event(client).get_json()['id']
    r = client.delete(
        f'/calendar/events/{event_id}',
        headers={'X-Fingerprint-ID': FINGERPRINT},
    )
    assert r.status_code == 200
    # Confirm it's gone
    assert client.get(f'/calendar/events/{event_id}').status_code == 404


def test_delete_event_wrong_fingerprint(client):
    event_id = post_event(client).get_json()['id']
    r = client.delete(
        f'/calendar/events/{event_id}',
        headers={'X-Fingerprint-ID': OTHER_FINGERPRINT},
    )
    assert r.status_code == 403


def test_delete_event_missing_fingerprint(client):
    event_id = post_event(client).get_json()['id']
    r = client.delete(f'/calendar/events/{event_id}')
    assert r.status_code == 400


def test_delete_event_not_found(client):
    r = client.delete(
        '/calendar/events/999',
        headers={'X-Fingerprint-ID': FINGERPRINT},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# missionary_type filtering
# ---------------------------------------------------------------------------

def test_get_events_filters_by_type(client):
    post_event(client, missionary_type='elders')
    post_event(client, missionary_type='sisters')
    r = client.get('/calendar/events?type=elders')
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 1
    assert data[0]['missionary_type'] == 'elders'


def test_get_events_no_filter_returns_all(client):
    post_event(client, missionary_type='elders')
    post_event(client, missionary_type='sisters')
    r = client.get('/calendar/events')
    assert r.status_code == 200
    assert len(r.get_json()) == 2


def test_post_event_missing_missionary_type(client):
    r = client.post(
        '/calendar/events',
        json={
            'phone_num': '0400000000',
            'f_name': 'Jane',
            'l_name': 'Smith',
            'time': '2099-06-01T12:00:00',
        },
        headers={'X-Fingerprint-ID': FINGERPRINT},
    )
    assert r.status_code == 400


def test_post_event_invalid_missionary_type(client):
    r = client.post(
        '/calendar/events',
        json={
            'phone_num': '0400000000',
            'f_name': 'Jane',
            'l_name': 'Smith',
            'time': '2099-06-01T12:00:00',
            'missionary_type': 'invalid',
        },
        headers={'X-Fingerprint-ID': FINGERPRINT},
    )
    assert r.status_code == 400

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health(client):
    r = client.get("/calendar/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"

def test_home_renders_with_no_data(logged_in_client, seeded):
    resp = logged_in_client.get("/")
    assert resp.status_code == 200
    assert b"Finances" in resp.data


def test_aspect_detail_renders(logged_in_client, seeded):
    resp = logged_in_client.get("/aspects/finances")
    assert resp.status_code == 200
    assert b"Expenditures" in resp.data


def test_aspect_detail_404_for_unknown_slug(logged_in_client, seeded):
    resp = logged_in_client.get("/aspects/does-not-exist")
    assert resp.status_code == 404


def test_status_indicator_reflects_target(logged_in_client, seeded, db):
    metric_id = str(seeded["monthly_metric"]["_id"])
    logged_in_client.post("/reviews/2026-08", data={f"metric_{metric_id}": "600"})
    resp = logged_in_client.get("/aspects/finances")
    assert b"On track" in resp.data

def test_today_form_renders(logged_in_client, seeded):
    resp = logged_in_client.get("/today")
    assert resp.status_code == 200
    assert b"Expenditures" in resp.data


def test_save_daily_entry(logged_in_client, seeded, db):
    metric_id = str(seeded["daily_metric"]["_id"])
    resp = logged_in_client.post(
        "/today", data={"date": "2026-08-10", f"metric_{metric_id}": "42.5"}, follow_redirects=True
    )
    assert resp.status_code == 200
    doc = db.entries.find_one({"metric_id": seeded["daily_metric"]["_id"]})
    assert doc["value"] == 42.5


def test_edit_past_day_via_query_param(logged_in_client, seeded):
    resp = logged_in_client.get("/today?date=2026-08-01")
    assert resp.status_code == 200
    assert b"August 01, 2026" in resp.data

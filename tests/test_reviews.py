def test_review_form_renders(logged_in_client, seeded):
    resp = logged_in_client.get("/reviews/2026-08")
    assert resp.status_code == 200
    assert b"What went well this month?" in resp.data


def test_review_save_and_reload(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    resp = logged_in_client.post(
        "/reviews/2026-08",
        data={
            f"highlights_{aspect_id}": "Stayed on budget",
            f"lowlights_{aspect_id}": "",
            f"focus_next_{aspect_id}": "Save more",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    review = db.reviews.find_one({"period_type": "monthly"})
    assert review["aspect_reflections"][0]["highlights"] == "Stayed on budget"

    reload_resp = logged_in_client.get("/reviews/2026-08")
    assert b"Stayed on budget" in reload_resp.data


def test_review_history_lists_saved_reviews(logged_in_client, seeded):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post("/reviews/2026-08", data={f"highlights_{aspect_id}": "ok"})
    resp = logged_in_client.get("/reviews/")
    assert b"August 2026" in resp.data


def test_monthly_metric_logged_via_review(logged_in_client, seeded, db):
    metric_id = str(seeded["monthly_metric"]["_id"])
    logged_in_client.post("/reviews/2026-08", data={f"metric_{metric_id}": "2500"})
    doc = db.entries.find_one({"metric_id": seeded["monthly_metric"]["_id"]})
    assert doc["value"] == 2500.0


def test_monthly_metric_value_prefills_on_reload(logged_in_client, seeded):
    metric_id = str(seeded["monthly_metric"]["_id"])
    logged_in_client.post("/reviews/2026-08", data={f"metric_{metric_id}": "2500"})
    resp = logged_in_client.get("/reviews/2026-08")
    assert b"2500" in resp.data

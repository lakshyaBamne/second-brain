def test_add_aspect(logged_in_client, db):
    resp = logged_in_client.post("/settings/aspects", data={"name": "Health"}, follow_redirects=True)
    assert resp.status_code == 200
    doc = db.life_aspects.find_one({"name": "Health"})
    assert doc is not None
    assert doc["color_light"]  # got a categorical slot assigned


def test_second_aspect_gets_a_different_color(logged_in_client, db, seeded):
    logged_in_client.post("/settings/aspects", data={"name": "Health"})
    finances = db.life_aspects.find_one({"name": "Finances"})
    health = db.life_aspects.find_one({"name": "Health"})
    assert finances["color_light"] != health["color_light"]


def test_add_metric(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    resp = logged_in_client.post(
        "/settings/metrics",
        data={"aspect_id": aspect_id, "name": "Net worth", "type": "number", "cadence": "monthly", "unit": "currency"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert db.metrics.find_one({"name": "Net worth"}) is not None


def test_archive_metric_hides_it_from_daily_form(logged_in_client, seeded, db):
    metric_id = str(seeded["daily_metric"]["_id"])
    logged_in_client.post(f"/settings/metrics/{metric_id}/archive")
    resp = logged_in_client.get("/today")
    assert b"Expenditures" not in resp.data


def test_delete_aspect_cascades_to_metrics(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(f"/settings/aspects/{aspect_id}/delete")
    assert db.life_aspects.find_one({"_id": seeded["aspect"]["_id"]}) is None
    assert db.metrics.count_documents({"aspect_id": seeded["aspect"]["_id"]}) == 0

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


def test_add_metric_with_weekly_cadence(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/settings/metrics",
        data={"aspect_id": aspect_id, "name": "Weekly mood", "type": "number", "cadence": "weekly"},
        follow_redirects=True,
    )
    doc = db.metrics.find_one({"name": "Weekly mood"})
    assert doc is not None
    assert doc["cadence"] == "weekly"


def test_edit_metric_updates_fields(logged_in_client, seeded, db):
    metric_id = str(seeded["monthly_metric"]["_id"])
    logged_in_client.post(
        f"/settings/metrics/{metric_id}/edit",
        data={
            "name": "Net worth",
            "type": "number",
            "cadence": "monthly",
            "unit": "USD",
            "target_value": "1000",
            "target_direction": "at_least",
        },
        follow_redirects=True,
    )
    doc = db.metrics.find_one({"_id": seeded["monthly_metric"]["_id"]})
    assert doc["name"] == "Net worth"
    assert doc["unit"] == "USD"
    assert doc["target"] == {"value": 1000.0, "direction": "at_least"}


def test_edit_metric_can_change_cadence(logged_in_client, seeded, db):
    metric_id = str(seeded["monthly_metric"]["_id"])
    logged_in_client.post(
        f"/settings/metrics/{metric_id}/edit",
        data={"name": "In-hand money", "type": "number", "cadence": "weekly", "unit": "currency"},
    )
    doc = db.metrics.find_one({"_id": seeded["monthly_metric"]["_id"]})
    assert doc["cadence"] == "weekly"


def test_archive_metric_hides_it_from_daily_form(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/settings/metrics",
        data={"aspect_id": aspect_id, "name": "Steps", "type": "number", "cadence": "daily"},
        follow_redirects=True,  # consume the "Added metric" flash so it doesn't leak into the next page's assertion
    )
    metric_id = str(db.metrics.find_one({"name": "Steps"})["_id"])
    logged_in_client.post(f"/settings/metrics/{metric_id}/archive")
    resp = logged_in_client.get("/today")
    assert b"Steps" not in resp.data


def test_add_aspect_with_custom_transaction_config(logged_in_client, db):
    logged_in_client.post(
        "/settings/aspects",
        data={
            "name": "Health",
            "enable_transactions": "on",
            "amount_label": "Hours",
            "categories": "Gym, Sports, Others",
        },
    )
    doc = db.life_aspects.find_one({"name": "Health"})
    assert doc["transaction_config"] == {"amount_label": "Hours", "categories": ["Gym", "Sports", "Others"]}


def test_add_aspect_dedupes_and_trims_categories(logged_in_client, db):
    logged_in_client.post(
        "/settings/aspects",
        data={"name": "Health", "enable_transactions": "on", "categories": " Gym ,Gym, Sports,,"},
    )
    doc = db.life_aspects.find_one({"name": "Health"})
    assert doc["transaction_config"]["categories"] == ["Gym", "Sports"]


def test_add_aspect_without_transactions_checkbox_has_no_config(logged_in_client, db):
    logged_in_client.post("/settings/aspects", data={"name": "Health"})
    doc = db.life_aspects.find_one({"name": "Health"})
    assert doc["transaction_config"] is None


def test_add_aspect_checkbox_without_categories_has_no_config(logged_in_client, db):
    logged_in_client.post("/settings/aspects", data={"name": "Health", "enable_transactions": "on"})
    doc = db.life_aspects.find_one({"name": "Health"})
    assert doc["transaction_config"] is None


def test_update_transaction_config_on_existing_aspect(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        f"/settings/aspects/{aspect_id}/transaction_config",
        data={"enable_transactions": "on", "amount_label": "Amount", "categories": "Groceries, Rent"},
    )
    doc = db.life_aspects.find_one({"_id": seeded["aspect"]["_id"]})
    assert doc["transaction_config"]["categories"] == ["Groceries", "Rent"]


def test_disable_transaction_config_on_existing_aspect(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(f"/settings/aspects/{aspect_id}/transaction_config", data={})
    doc = db.life_aspects.find_one({"_id": seeded["aspect"]["_id"]})
    assert doc["transaction_config"] is None


def test_delete_aspect_cascades_to_metrics_and_transactions(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-10",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_amount": "5",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
    )
    logged_in_client.post(f"/settings/aspects/{aspect_id}/delete")
    assert db.life_aspects.find_one({"_id": seeded["aspect"]["_id"]}) is None
    assert db.metrics.count_documents({"aspect_id": seeded["aspect"]["_id"]}) == 0
    assert db.transactions.count_documents({"aspect_id": seeded["aspect"]["_id"]}) == 0

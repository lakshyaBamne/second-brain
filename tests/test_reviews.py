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


def test_review_collates_transactions_by_category(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-10",
            f"txn_count_{aspect_id}": "3",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_amount": "5",
            f"txn_{aspect_id}_0_category": "Expenditure",
            f"txn_{aspect_id}_1_name": "Groceries",
            f"txn_{aspect_id}_1_amount": "45",
            f"txn_{aspect_id}_1_category": "Expenditure",
            f"txn_{aspect_id}_2_name": "401k",
            f"txn_{aspect_id}_2_amount": "200",
            f"txn_{aspect_id}_2_category": "Investments",
        },
    )
    resp = logged_in_client.get("/reviews/2026-08")
    assert resp.status_code == 200
    assert b"50.00" in resp.data  # 5 + 45 expenditure total
    assert b"200.00" in resp.data  # investments total


def test_review_transaction_totals_exclude_other_months(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-07-15",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Last month's spend",
            f"txn_{aspect_id}_0_amount": "999",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
    )
    resp = logged_in_client.get("/reviews/2026-08")
    assert b"999.00" not in resp.data

def test_today_renders_transaction_section(logged_in_client, seeded):
    resp = logged_in_client.get("/today")
    assert resp.status_code == 200
    assert b"Transactions" in resp.data
    assert b"Expenditure" in resp.data


def test_add_single_transaction(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    resp = logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_description": "Morning espresso",
            f"txn_{aspect_id}_0_amount": "4.5",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = db.transactions.find_one({"name": "Coffee"})
    assert doc is not None
    assert doc["amount"] == 4.5
    assert doc["category"] == "Expenditure"
    assert doc["description"] == "Morning espresso"


def test_add_multiple_transactions_in_one_save(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    resp = logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "2",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_description": "",
            f"txn_{aspect_id}_0_amount": "4.5",
            f"txn_{aspect_id}_0_category": "Expenditure",
            f"txn_{aspect_id}_1_name": "Stock buy",
            f"txn_{aspect_id}_1_description": "",
            f"txn_{aspect_id}_1_amount": "100",
            f"txn_{aspect_id}_1_category": "Investments",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert db.transactions.count_documents({}) == 2


def test_transaction_missing_required_field_is_skipped(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "",  # no name
            f"txn_{aspect_id}_0_amount": "10",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
    )
    assert db.transactions.count_documents({}) == 0


def test_added_transaction_shows_on_reload(logged_in_client, seeded):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_amount": "4.5",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
    )
    resp = logged_in_client.get("/today?date=2026-08-16")
    assert b"Coffee" in resp.data


def test_transaction_delete_control_does_not_nest_a_form(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_amount": "4.5",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
    )
    html = logged_in_client.get("/today?date=2026-08-16").data.decode()
    main_html = html.split('<main', 1)[1]
    # A nested <form> here (e.g. wrapping the delete button) makes browsers
    # auto-close the outer form at that point per the HTML parsing spec,
    # silently detaching "Save today's entries" (and anything after it)
    # from the form once any transaction exists — regression test for that.
    assert main_html.count("<form") == 1
    assert "/today/transactions/" in main_html
    assert "formaction=" in main_html


def test_delete_transaction(logged_in_client, seeded, db):
    aspect_id = str(seeded["aspect"]["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Coffee",
            f"txn_{aspect_id}_0_amount": "4.5",
            f"txn_{aspect_id}_0_category": "Expenditure",
        },
    )
    txn_id = str(db.transactions.find_one({"name": "Coffee"})["_id"])
    resp = logged_in_client.post(
        f"/today/transactions/{txn_id}/delete", data={"date": "2026-08-16"}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert db.transactions.count_documents({}) == 0


def test_weekly_metric_not_shown_on_today_page(logged_in_client, seeded, db):
    from app.models.metrics import create_metric

    create_metric(db, seeded["aspect"]["_id"], "Weekly mood", "number", "weekly")
    resp = logged_in_client.get("/today")
    assert b"Weekly mood" not in resp.data


def test_edit_past_day_via_query_param(logged_in_client, seeded):
    resp = logged_in_client.get("/today?date=2026-08-01")
    assert resp.status_code == 200
    assert b"August 01, 2026" in resp.data


def test_today_date_picker_reflects_viewed_date(logged_in_client, seeded):
    resp = logged_in_client.get("/today?date=2026-08-01")
    assert b'type="date" value="2026-08-01"' in resp.data


def test_editing_past_day_metric_value_overwrites_not_duplicates(logged_in_client, seeded, db):
    from app.models.metrics import create_metric

    metric = create_metric(db, seeded["aspect"]["_id"], "Mood", "number", "daily")
    logged_in_client.post("/today", data={"date": "2026-08-10", f"metric_{metric['_id']}": "3"})
    logged_in_client.post("/today", data={"date": "2026-08-10", f"metric_{metric['_id']}": "9"})

    assert db.entries.count_documents({"metric_id": metric["_id"]}) == 1
    doc = db.entries.find_one({"metric_id": metric["_id"]})
    assert doc["value"] == 9.0

    reload_resp = logged_in_client.get("/today?date=2026-08-10")
    assert b'value="9.0"' in reload_resp.data

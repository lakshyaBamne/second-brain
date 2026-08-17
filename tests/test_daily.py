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


def test_edit_past_day_via_query_param(logged_in_client, seeded):
    resp = logged_in_client.get("/today?date=2026-08-01")
    assert resp.status_code == 200
    assert b"August 01, 2026" in resp.data

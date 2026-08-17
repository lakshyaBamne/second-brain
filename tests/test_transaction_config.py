from app.models.life_aspects import create_aspect


def _make_health_aspect(db):
    return create_aspect(
        db,
        "Health",
        transaction_config={"amount_label": "Hours", "categories": ["Gym", "Sports", "Others"]},
    )


def test_today_shows_custom_amount_label_and_categories(logged_in_client, db):
    _make_health_aspect(db)
    resp = logged_in_client.get("/today")
    assert resp.status_code == 200
    assert b"Hours" in resp.data
    assert b"Gym" in resp.data
    assert b"Sports" in resp.data
    assert b"Others" in resp.data
    # the Finances-only Expenditure/Investments categories shouldn't leak into Health's dropdown
    assert resp.data.count(b'value="Gym"') == 1


def test_add_transaction_with_custom_category(logged_in_client, db):
    aspect = _make_health_aspect(db)
    aspect_id = str(aspect["_id"])
    resp = logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Leg day",
            f"txn_{aspect_id}_0_amount": "1.5",
            f"txn_{aspect_id}_0_category": "Gym",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    doc = db.transactions.find_one({"name": "Leg day"})
    assert doc["category"] == "Gym"
    assert doc["amount"] == 1.5


def test_category_outside_configured_list_is_rejected(logged_in_client, db):
    aspect = _make_health_aspect(db)
    aspect_id = str(aspect["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Sneaky",
            f"txn_{aspect_id}_0_amount": "1",
            f"txn_{aspect_id}_0_category": "Expenditure",  # not one of Health's categories
        },
    )
    assert db.transactions.count_documents({}) == 0


def test_two_aspects_keep_independent_transaction_configs(logged_in_client, seeded, db):
    # seeded already created Finances with Expenditure/Savings/Investments/Debt
    health = _make_health_aspect(db)
    finance_id = str(seeded["aspect"]["_id"])
    health_id = str(health["_id"])

    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-16",
            f"txn_count_{finance_id}": "1",
            f"txn_{finance_id}_0_name": "Coffee",
            f"txn_{finance_id}_0_amount": "5",
            f"txn_{finance_id}_0_category": "Expenditure",
            f"txn_count_{health_id}": "1",
            f"txn_{health_id}_0_name": "Run",
            f"txn_{health_id}_0_amount": "1",
            f"txn_{health_id}_0_category": "Sports",
        },
    )
    assert db.transactions.count_documents({"category": "Expenditure"}) == 1
    assert db.transactions.count_documents({"category": "Sports"}) == 1


def test_review_collates_health_by_its_own_categories(logged_in_client, db):
    aspect = _make_health_aspect(db)
    aspect_id = str(aspect["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-10",
            f"txn_count_{aspect_id}": "2",
            f"txn_{aspect_id}_0_name": "Leg day",
            f"txn_{aspect_id}_0_amount": "1.5",
            f"txn_{aspect_id}_0_category": "Gym",
            f"txn_{aspect_id}_1_name": "5k run",
            f"txn_{aspect_id}_1_amount": "0.5",
            f"txn_{aspect_id}_1_category": "Sports",
        },
    )
    resp = logged_in_client.get("/reviews/2026-08")
    assert resp.status_code == 200
    assert b"Hours, by category" in resp.data
    assert b"1.50" in resp.data
    assert b"0.50" in resp.data

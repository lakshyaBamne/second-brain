def test_home_renders_with_no_data(logged_in_client, seeded):
    resp = logged_in_client.get("/")
    assert resp.status_code == 200
    assert b"Finances" in resp.data


def test_aspect_detail_renders(logged_in_client, seeded):
    resp = logged_in_client.get("/aspects/finances")
    assert resp.status_code == 200
    assert b"In-hand money" in resp.data


def test_aspect_detail_404_for_unknown_slug(logged_in_client, seeded):
    resp = logged_in_client.get("/aspects/does-not-exist")
    assert resp.status_code == 404


def test_status_indicator_reflects_target(logged_in_client, seeded, db):
    metric_id = str(seeded["monthly_metric"]["_id"])
    logged_in_client.post("/reviews/2026-08", data={f"metric_{metric_id}": "600"})
    resp = logged_in_client.get("/aspects/finances")
    assert b"On track" in resp.data


def test_aspect_detail_shows_transaction_totals(logged_in_client, seeded):
    aspect_id = str(seeded["aspect"]["_id"])
    for day in ("2026-08-16", "2026-08-17"):
        logged_in_client.post(
            "/today",
            data={
                "date": day,
                f"txn_count_{aspect_id}": "1",
                f"txn_{aspect_id}_0_name": "Groceries",
                f"txn_{aspect_id}_0_amount": "10",
                f"txn_{aspect_id}_0_category": "Expenditure",
            },
        )
    resp = logged_in_client.get("/aspects/finances")
    assert resp.status_code == 200
    assert b"by category" in resp.data
    assert b"20.00" in resp.data
    # the metric card (no entries logged for it) still renders its own empty state
    assert b"No entries yet for this period." in resp.data


def test_home_card_shows_transaction_total_for_aspect_without_metrics(logged_in_client, seeded, db):
    from app.models.life_aspects import create_aspect

    aspect = create_aspect(
        db, "Health", transaction_config={"amount_label": "Hours", "categories": ["Gym", "Sports", "Others"]}
    )
    aspect_id = str(aspect["_id"])
    logged_in_client.post(
        "/today",
        data={
            "date": "2026-08-17",
            f"txn_count_{aspect_id}": "1",
            f"txn_{aspect_id}_0_name": "Football",
            f"txn_{aspect_id}_0_amount": "1.5",
            f"txn_{aspect_id}_0_category": "Sports",
        },
    )
    resp = logged_in_client.get("/")
    assert resp.status_code == 200
    assert b"Health" in resp.data
    assert b"1.50" in resp.data
    assert b"No metrics yet." not in resp.data

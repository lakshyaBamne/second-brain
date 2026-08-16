import mongomock
import pytest

from app import create_app
from app.db import ensure_indexes
from app.models.life_aspects import create_aspect
from app.models.metrics import create_metric
from app.models.users import create_user


@pytest.fixture
def db():
    client = mongomock.MongoClient()
    database = client["second_brain_test"]
    ensure_indexes(database)
    return database


@pytest.fixture
def app(db):
    return create_app(db=db, config_overrides={"TESTING": True, "SECRET_KEY": "test", "WTF_CSRF_ENABLED": False})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded(db):
    create_user(db, "test@example.com", "password123")
    aspect = create_aspect(db, "Finances")
    daily_metric = create_metric(db, aspect["_id"], "Expenditures", "number", "daily", "currency")
    monthly_metric = create_metric(
        db, aspect["_id"], "Savings", "number", "monthly", "currency", {"value": 500, "direction": "at_least"}
    )
    return {"aspect": aspect, "daily_metric": daily_metric, "monthly_metric": monthly_metric}


@pytest.fixture
def logged_in_client(client, seeded):
    client.post("/login", data={"email": "test@example.com", "password": "password123"})
    return client

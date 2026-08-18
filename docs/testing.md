# Testing

```
pytest                              # run everything
pytest tests/test_daily.py          # one file
pytest tests/test_daily.py::test_name   # one test
```

Tests run against `mongomock` (an in-memory Mongo fake), never a real
database — there's no test-database setup/teardown to manage, and CI (if
added) needs no external services for this suite to pass.

## Fixture chain (`tests/conftest.py`)

```
db                → fresh mongomock database, indexes applied via ensure_indexes
app(db)           → Flask app built with create_app(db=db, config_overrides={
                       TESTING: True, SECRET_KEY: "test", WTF_CSRF_ENABLED: False
                     })
client(app)       → app.test_client()
seeded(db)        → creates test@example.com / password123, a "Finances" aspect
                     WITH transaction_config already set (categories:
                     Expenditure/Savings/Investments/Debt), and one monthly
                     metric "In-hand money" (target: >= 500)
logged_in_client(client, seeded) → client, already POSTed /login as the seeded user
```

Each test file corresponds roughly to one blueprint/feature area:

| File | Covers |
|---|---|
| `test_auth.py` | login/logout |
| `test_daily.py` | Today page: metric entry, transaction add/delete |
| `test_dashboard.py` | dashboard summary cards |
| `test_reviews.py` | monthly + weekly review read/write, review history cards, metric + transaction rollups |
| `test_settings.py` | aspect/metric CRUD, edit, archive/reactivate |
| `test_transaction_config.py` | the configurable (non-Finances) transaction log — custom `amount_label`/`categories` per aspect, e.g. a "Health" aspect tracking Gym/Sports/Others in hours |

## Conventions to follow when adding tests

- **CSRF is off by default** in the `app` fixture — don't add
  `csrf_token` to test form posts unless you're specifically testing CSRF
  behavior (in which case override `WTF_CSRF_ENABLED` for that test).
- **Model-level tests** call `app/models/*.py` functions directly against
  the `db` fixture (no HTTP involved) — use this style for testing data
  logic in isolation (e.g. cascading delete, index uniqueness behavior).
- **Route-level tests** go through `client`/`logged_in_client` and assert
  on `resp.status_code` / `resp.data` (byte-string `in` checks) or query
  `db` directly afterward to confirm a write happened — see
  `test_transaction_config.py::test_add_transaction_with_custom_category`
  for the pattern: POST to the route, then `db.transactions.find_one(...)`
  to assert on the persisted document.
- **Don't hand-build ObjectId strings or dates** — use the model functions
  (`create_aspect`, `create_metric`, etc.) to set up fixtures within a test,
  the same way `seeded` does, rather than inserting raw dicts into
  `mongomock` collections.
- When testing something that depends on "today"/date math, prefer passing
  an explicit `date` (form field or function arg) over relying on
  `date.today()`, so the test doesn't become time-of-run-dependent — most
  existing tests already do this (e.g. `"date": "2026-08-16"` in POST
  bodies).

## What's not covered

There's no browser/UI test layer — the client-side transaction staging
(`app/static/js/transactions.js`) is exercised indirectly via the
server-side form-field contract it produces (see
[`frontend.md#transaction-quick-add-js`](frontend.md#transaction-quick-add-js)),
not via a JS test runner or headless browser. If you change that JS file's
behavior, manually verify in a browser (`python wsgi.py`) — the automated
suite won't catch a staging/UI regression there, only a mismatch between
the JS's field-naming contract and what `save_today` parses (and even then,
only if a test happens to submit the field names your change broke).

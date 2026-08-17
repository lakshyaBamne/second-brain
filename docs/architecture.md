# Architecture & Project Structure

## Stack

- **Backend**: Flask 3, Python, no async.
- **Database**: MongoDB via `pymongo` (no ODM/ORM — model modules are thin
  wrappers around raw collection calls).
- **Auth**: Flask-Login, session-cookie based, single-tenant-oriented (there
  is no notion of roles/teams — see [`database.md`](database.md#users)).
- **Frontend**: server-rendered Jinja2 templates, Tailwind CSS via CDN
  `<script>` tag (no `npm`/build step, no `tailwind.config.js`), Chart.js via
  CDN, a small amount of hand-written vanilla JS for interactive bits.
- **Tests**: `pytest` against `mongomock` (an in-memory Mongo fake) — no
  real database needed to run the suite.

There is no frontend build pipeline, no bundler, no TypeScript, and no ORM
migration framework. Schema changes to Mongo documents are handled with
one-off scripts at the repo root (see
[`database.md#migrations`](database.md#migrations)).

## Directory layout

```
app/
  __init__.py          # App factory: create_app()
  config.py            # Config class, reads from env vars
  db.py                # get_db(), ensure_indexes()
  colors.py            # Fixed categorical color palette + slot assignment
  analytics.py         # Derived data for the dashboard (sparklines, status)
  blueprints/
    auth/routes.py      # /login, /logout
    daily/routes.py      # /today — daily metric entry + quick-add transactions
    dashboard/routes.py  # / and /aspects/<slug> — overview + per-aspect charts
    reviews/routes.py    # /reviews — monthly review read/write
    settings/routes.py   # /settings/aspects, /settings/metrics — CRUD/config UI
  models/
    users.py, life_aspects.py, metrics.py, entries.py, transactions.py, reviews.py
  templates/            # Jinja2, one subdir per blueprint + base.html
  static/js/             # charts.js, transactions.js — no build step

tests/
  conftest.py           # db / app / client / seeded / logged_in_client fixtures
  test_*.py             # one file roughly per blueprint/feature

seed.py                          # one-time: create login + seed Finances aspect
migrate_transactions.py          # one-off: old bool flag -> transaction_config
migrate_configurable_transactions.py  # one-off: re-case legacy category strings
wsgi.py                          # entrypoint: python wsgi.py
project-prompt-v1.0.0.md         # original product/design doc
```

## Request flow

1. `wsgi.py` loads `.env` (via `python-dotenv`) and calls
   `app.create_app()`.
2. `create_app()` (`app/__init__.py`) builds the Flask app, loads `Config`,
   connects to Mongo (`app.db = get_db(...)`), runs
   `ensure_indexes(app.db)`, sets up `CSRFProtect` and `Flask-Login`, and
   registers all five blueprints.
3. A request hits a blueprint route
   (`app/blueprints/<name>/routes.py`). Routes are `@login_required` except
   `auth.login`.
4. The route calls one or more **model functions**
   (`app/models/*.py`), passing `current_app.db` explicitly as the first
   argument — there's no global DB singleton or request-scoped session
   object beyond `app.db`.
5. Model functions run plain `pymongo` calls (`find`, `find_one`,
   `update_one` with `upsert=True`, etc.) and return plain dicts (raw Mongo
   documents) or lists of them — never a custom model class (the one
   exception is `models/users.py::User`, a thin `UserMixin` wrapper needed
   by Flask-Login).
6. The route renders a Jinja2 template with those dicts, or redirects.

There is **no service layer** between routes and models — routes contain
the orchestration logic (looping over aspects, branching on
`transaction_config`, etc.) directly. Keep that pattern when adding routes;
don't introduce a services/ layer for a single new feature.

## Key cross-cutting concepts

- **Life aspects are the top-level organizing unit**, and they're entirely
  user-configurable (created/edited/deleted from Settings, not from code).
  Every other collection (`metrics`, `transactions`) hangs off an aspect via
  `aspect_id`, and deleting an aspect cascades to delete its metrics,
  entries, and transactions (`life_aspects.delete_aspect`).
- **The quick-add transaction log is opt-in per aspect** via
  `aspect.transaction_config` (`None` = disabled). This is the most
  actively-developed feature in the current branch — see
  [`database.md#transactions`](database.md#transactions) and
  [`extending.md`](extending.md) for the full shape and how it plugs into
  the Today page and monthly reviews.
- **Colors are assigned, never chosen**: `app/colors.py` holds a fixed,
  colorblind-safe categorical palette; each new aspect gets
  `slot_for_order(order)`, so aspect colors are deterministic and consistent
  across light/dark mode.
- **Dates are always normalized** before being used as Mongo query/sort
  keys — daily entries key off midnight-of-day (`entries.day_key`), monthly
  data keys off midnight-of-the-1st (`entries.month_key`). Passing a raw
  `date`/`datetime` instead of running it through these helpers will silently
  break the unique index on `entries` and any range queries.

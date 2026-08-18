# Backend (Python)

This covers everything under `app/` except templates/static assets (see
[`frontend.md`](frontend.md)) and the document shapes themselves (see
[`database.md`](database.md)).

## App factory — `app/__init__.py`

```python
def create_app(db=None, config_overrides=None):
    ...
```

- `db=None` — pass a `mongomock` database (tests) or leave unset to connect
  to real Mongo via `Config.MONGO_URI`/`MONGO_DBNAME`. This is the seam that
  makes the whole app testable without a live database
  (see [`testing.md`](testing.md)).
- `config_overrides` — a dict merged into `app.config` after loading
  `Config`; tests use this for `TESTING`, `SECRET_KEY`, `WTF_CSRF_ENABLED`.
- Registers `CSRFProtect` (Flask-WTF) globally — every POST form in the
  templates includes a hidden `csrf_token` field; new forms must too, or
  the request will 400.
- Registers `Flask-Login` with a `user_loader` backed by
  `models.users.get_user_by_id`.
- Registers all five blueprints (`auth`, `daily`, `dashboard`, `reviews`,
  `settings`) — see below.
- Injects `current_year` into every template via `context_processor`.

## Config — `app/config.py`

Plain class, values pulled from environment variables (loaded from `.env`
via `python-dotenv` in `wsgi.py`/`seed.py`, not in `config.py` itself).
`SESSION_COOKIE_SECURE` defaults to `false` so local `http://127.0.0.1` dev
still works — set it `true` in production over HTTPS.

## `app/db.py`

- `get_db(uri, db_name)` — thin `MongoClient` wrapper, 5s server selection
  timeout.
- `ensure_indexes(db)` — the **single source of truth** for all Mongo
  indexes, called on every `create_app()` (including in tests against
  `mongomock`). If you add a new query pattern that needs an index, add it
  here — there's no separate migration mechanism for indexes.

## Blueprints (`app/blueprints/<name>/routes.py`)

Each blueprint is a `routes.py` file with a Flask `Blueprint` and its view
functions — there are no separate `forms.py`/`services.py` files per
blueprint. Business logic that isn't pure data access lives directly in the
route function.

| Blueprint | URL prefix | Responsibility |
|---|---|---|
| `auth` | `/` (`/login`, `/logout`) | Login/logout via Flask-Login |
| `daily` | `/today` | Log today's (or any day's) metric values; add/delete quick-add transactions |
| `dashboard` | `/` | Home overview (one card per aspect, sparkline of its headline metric) + per-aspect detail with range-filtered charts |
| `reviews` | `/reviews` | List + fill out monthly and weekly reviews (reflection prompts, cadence-matched metric inputs, transaction category totals on the monthly page) |
| `settings` | `/settings` | CRUD for life aspects (incl. `transaction_config`) and metrics (incl. archive/reactivate) |

Notable route-level patterns:

- **`daily.today` (GET/POST)** builds one "group" per aspect combining its
  daily metrics *and* (if enabled) its transaction log for that day, then
  skips the group entirely if it has neither
  (`app/blueprints/daily/routes.py:39`). The POST handler iterates all
  aspects again and, per aspect, both upserts metric entries and inserts any
  staged transactions (`txn_count_<aspect_id>` + indexed `txn_<aspect_id>_<i>_<field>`
  form fields — see [`frontend.md`](frontend.md#transaction-quick-add-js)
  for how the JS stages those before submit). `_parse_date` defaults to
  today but accepts a `?date=` query param, so viewing/editing any past
  day's log is just navigating there (the template's prev/next arrows and
  date-picker input both do this) — upserting on the same `(metric_id,
  date)` means re-saving a past day overwrites rather than duplicates, and
  every other page (dashboard, reviews) reads `entries` live, so an edit to
  a past day is reflected everywhere immediately with no cache to bust.
- **`daily.delete_transaction` (POST)** deletes one transaction and redirects
  back to `?date=<the day it was on>`. Its button lives inside the *same*
  outer form as everything else on the page via `formaction`/`formmethod`,
  not a separate nested `<form>` — see
  [`frontend.md#never-nest-a-form-inside-another-form`](frontend.md#never-nest-a-form-inside-another-form)
  for why that distinction matters (it was a real, hard-to-spot bug).
- **`reviews.history` (GET)** builds one card per month (always including
  the current month, plus any month with a saved monthly or weekly review)
  in reverse-chronological order, each holding 4 week sub-cards + 1 month
  sub-card computed via `_week_bounds`/`_week_num_for_day`
  (see [`database.md#reviews`](database.md#reviews) for the week-bucket
  scheme). The current month and current week are flagged `is_current` for
  the template to highlight.
- **`reviews.review` (GET/POST)** — the monthly review. Computes, per
  aspect, this-month vs. last-month averages for every **non-weekly**
  metric (`cadence == "weekly"` metrics are skipped entirely so they never
  leak into the monthly chart) and, if `transaction_config` is set,
  this-month vs. last-month totals per category
  (`transactions_model.totals_by_category`). POST saves free-text
  reflections and any monthly-cadence metric values in one upsert.
- **`reviews.weekly_review` (GET/POST)**, at `/reviews/<period>/week/<1-4>`
  — the weekly counterpart. Same reflection-prompt shape (different
  wording, `WEEKLY_PROMPTS`) plus an input field per `cadence == "weekly"`
  metric for that aspect; nothing else (no charts, no transaction rollup —
  keep it lightweight). This is the *only* place a weekly-cadence metric's
  value can be entered or displayed.
- **`settings._parse_transaction_config(form)`** is the single place that
  turns raw form input into a `transaction_config` dict (or `None`) —
  reused by both "create aspect" and "update transaction config" POST
  handlers. If you add a new form that can set/edit this field, reuse this
  helper rather than re-parsing.
- **`dashboard.home`** picks each aspect's *first non-weekly* metric
  (filtered then indexed `[0]`, ordered by `order`) as its "headline" metric
  for the summary card — there's no explicit "primary metric" flag, order in
  the metrics list decides it. `dashboard.aspect_detail`'s per-metric chart
  loop applies the same `cadence != "weekly"` filter.
- **`settings.edit_metric` (POST)** rewrites all of a metric's editable
  fields (`name`/`type`/`cadence`/`unit`/`target`) in one `$set` via
  `metrics_model.update_metric` — the only settings route that lets you
  change a metric after creation instead of archiving and re-adding it.

## Models (`app/models/*.py`)

Plain functions, no classes (except `User`), first argument is always `db`.
Every function does exactly one Mongo operation or a small composition of
them — there's no query builder or repository abstraction. See
[`database.md`](database.md) for the full document shape each module
manages.

| Module | Manages |
|---|---|
| `users.py` | `users` collection; `User(UserMixin)` wraps a doc for Flask-Login |
| `life_aspects.py` | `life_aspects` collection; slug generation, color assignment, cascading delete |
| `metrics.py` | `metrics` collection; `METRIC_TYPES`/`CADENCES` constants, archive/reactivate (soft delete) |
| `entries.py` | `entries` collection; `day_key`/`month_key` date normalization — **always** go through these before querying/writing |
| `transactions.py` | `transactions` collection; `totals_by_category` powers the review-page rollup |
| `reviews.py` | `reviews` collection; cadence-agnostic — `get_review`/`upsert_review`/`list_reviews` all take `period_type` (`"monthly"` or `"weekly"`), one upsert per `(period_type, period_start)` |

When adding a model function, match the existing signature style: take
`db` first, take an `_id` as a plain string or `ObjectId` (model functions
generally accept a string and call `ObjectId(...)` internally — check the
specific module), return the raw dict/list rather than wrapping it.

## `app/analytics.py`

Sits above `entries.py`, used only by the dashboard blueprint:

- `sparkline_series(db, metric, days=30)` — last N days of a metric's
  entries as `[{date: "YYYY-MM-DD", value}, ...]`, fed straight into
  Chart.js as JSON (see [`frontend.md`](frontend.md#charts)).
- `status_for_metric(db, metric)` — `"good"` / `"warning"` / `None`,
  comparing the metric's latest value against its `target` (`{value,
  direction}`, where `direction` is `"at_least"` or `"at_most"`). Only
  meaningful for numeric metrics with a target set.

## `app/colors.py`

Fixed, validated, colorblind-safe categorical palette (see the `dataviz`
skill's `references/palette.md` for how it was derived) plus a status
palette (`good`/`warning`/`serious`/`critical`) and chrome/ink tokens for
light/dark mode. `slot_for_order(order)` deterministically maps the Nth
(0-indexed) life aspect to a palette slot — **never** hand-assign or store
an arbitrary color; always go through this function so palette changes
propagate everywhere automatically.

## Entrypoint scripts (repo root)

- `wsgi.py` — loads `.env`, builds the app via `create_app()`, runs the
  dev server on `0.0.0.0:5000` with `debug=True`. This is also what a
  production WSGI server (gunicorn, per `requirements.txt`) would import
  `app` from.
- `seed.py` — interactive one-time setup: creates the first login (skips if
  a user already exists) and the Finances aspect + its one manual metric
  (skips if `finances` slug already exists). Safe to re-run.
- `migrate_transactions.py`, `migrate_configurable_transactions.py` —
  one-off schema-migration scripts for databases seeded under an earlier
  version of the transaction-log feature. See
  [`database.md#migrations`](database.md#migrations). Not part of the
  regular dev workflow — only relevant when upgrading an old database.

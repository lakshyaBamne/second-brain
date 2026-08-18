# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Second Brain: a personal growth tracker. Daily entries roll up into monthly
reviews, per "life aspect" (e.g. Finances, Health). Flask + MongoDB +
Tailwind (CDN) + Chart.js (CDN) — no JS framework, no frontend build step.
See `project-prompt-v1.0.0.md` for the original design doc/scope and
`README.md` for setup instructions. `docs/` has a fuller, section-by-section
reference (architecture, backend, database, frontend, testing, extending) —
this file is the condensed version; check `docs/` when you need more detail
than fits here, and keep both in sync when either goes stale.

## Commands

```
# Run the app (needs MongoDB running — start-mongodb.bat starts a local
# portable instance on 127.0.0.1:27017)
python wsgi.py

# Run all tests (uses mongomock, no real DB needed)
pytest

# Run a single test file / test
pytest tests/test_daily.py
pytest tests/test_daily.py::test_name

# Seed a fresh DB (creates login user + Finances aspect + one metric)
python seed.py
```

There is no lint/format/typecheck command configured in this repo.

## Architecture

**App factory**: `app/__init__.py` builds the Flask app, attaches the Mongo
`db` handle directly to `app.db` (no Flask-SQLAlchemy-style ORM), and
registers blueprints. Tests inject a `mongomock` database via
`create_app(db=...)` (see `tests/conftest.py`) so the whole app runs against
an in-memory Mongo fake with no real database needed.

**Layering**: `app/blueprints/<name>/routes.py` (views) → `app/models/*.py`
(data access, plain functions taking `db` as the first arg, no classes/ORM)
→ raw pymongo collections. Routes call model functions directly; there is no
service layer. `app/analytics.py` sits above the entries model to compute
derived data (sparklines, on-track status) for the dashboard.

**Collections and their model modules**:
- `life_aspects` (`app/models/life_aspects.py`) — top-level categories
  (Finances, Health, ...), each with a slug, an assigned color (see below),
  and an optional `transaction_config`.
- `metrics` (`app/models/metrics.py`) — trackable values under an aspect.
  `type` is `number`/`boolean`/`rating`; `cadence` is
  `daily`/`weekly`/`monthly`. Metrics can be archived (soft-deleted via
  `active: False`) rather than deleted, to preserve history. `weekly`
  metrics are deliberately invisible everywhere except their weekly review
  page — filtered out of Today, the dashboard, and the monthly review.
- `entries` (`app/models/entries.py`) — one value per `(metric_id, date)`,
  upserted. `date` is always normalized to midnight via `day_key`/`month_key`
  before querying/writing — always go through these helpers rather than
  passing raw `date`/`datetime` objects. A weekly metric's single
  per-period entry lives at its week-bucket's start date, the same pattern
  monthly metrics use with `month_key`.
- `transactions` (`app/models/transactions.py`) — free-form
  name/description/amount/category log entries under an aspect, only used
  when that aspect's `transaction_config` is set (the "quick-add log"
  feature). Categories are per-aspect custom strings, not a fixed enum.
- `reviews` (`app/models/reviews.py`) — one document per period keyed by
  `(period_type, period_start)`, `period_type` is `"monthly"` or `"weekly"`,
  holding per-aspect reflection text plus whatever cadence-matched metrics
  were filled in for that period. A month is split into 4 fixed weekly
  buckets (days 1–7/8–14/15–21/22–end, not calendar Mon–Sun weeks) — see
  `reviews/routes.py::_week_bounds`. The Reviews page shows the current
  month as its own card (current week highlighted) plus past months below
  in reverse-chronological order, each with 4 week sub-cards + 1 month
  sub-card.
- `users` (`app/models/users.py`) — Flask-Login `UserMixin` wrapper around a
  `users` doc; single-user-oriented (no roles/permissions).

Indexes for all of the above are defined once in `app/db.py::ensure_indexes`
and applied on every `create_app` call (including in tests).

**Life aspects are user-configurable, not hardcoded**: new aspects, metrics,
and quick-add-log (`transaction_config`) are all created via Settings UI, no
code changes needed. When an aspect is deleted, `life_aspects.delete_aspect`
cascades: it deletes that aspect's metrics, entries, and transactions too.

**Colors**: `app/colors.py` holds a fixed, colorblind-safe categorical
palette (see the `dataviz` skill's `references/palette.md`). New aspects get
the next slot in order (`slot_for_order`) — colors are never hand-picked or
stored ad hoc.

**Quick-add transaction log**: an aspect can opt into a free-form
transaction log (`transaction_config = {amount_label, categories}`,
`None` when disabled). When enabled, the Today page
(`app/blueprints/daily/routes.py`) renders an add-transaction form
alongside daily metrics, and monthly reviews
(`app/blueprints/reviews/routes.py`) roll transactions up into
per-category totals (this month vs. last month). This replaced an earlier
fixed-metric approach to tracking finances (Expenditure/Savings/etc. as
`metrics` docs) — `migrate_transactions.py` and
`migrate_configurable_transactions.py` are one-off scripts for migrating
databases seeded under the old scheme; they archive (not delete) the old
metrics to preserve history.

**Templates**: server-rendered Jinja2 (`app/templates/`), Tailwind via CDN
class names, no build step. Chart.js (CDN) renders sparklines/charts from
JSON series data computed in `app/analytics.py`/route handlers. **Never nest
a `<form>` inside another `<form>`** (e.g. a delete button inside a page-wide
form) — browsers silently truncate the outer form at the nested one's
closing tag, breaking everything after it with no console error. Give the
button its own `formaction`/`formmethod` instead; see
`docs/frontend.md#never-nest-a-form-inside-another-form`.

## Testing conventions

Tests use `pytest` fixtures from `tests/conftest.py`:
- `db` — fresh `mongomock` database per test.
- `app` / `client` — Flask app/test client wired to that `db`, CSRF disabled.
- `seeded` — creates a test user plus a Finances aspect (with
  `transaction_config` already set) and one monthly metric.
- `logged_in_client` — a `client` already logged in as the `seeded` user.

Grep existing tests in `tests/` for the pattern before adding new ones —
model-level tests call `app/models/*.py` functions directly against the
`db` fixture; route-level tests go through `client`/`logged_in_client`.

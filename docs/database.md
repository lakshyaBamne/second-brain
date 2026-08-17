# Database (MongoDB)

No ODM — `app.db` is a raw `pymongo` `Database` handle (or a `mongomock`
equivalent in tests), and model modules (`app/models/*.py`) call collection
methods directly. There is no schema enforcement at the DB layer beyond the
indexes in `app/db.py::ensure_indexes`; validation happens in route/model
code before a document is written.

Connection: `MONGO_URI` / `MONGO_DBNAME` env vars (see `.env.example`),
resolved in `app/config.py` and `app/db.py::get_db`.

## Collections

### `users`

```
{
  _id: ObjectId,
  email: str,             # lowercased, unique
  password_hash: str,     # werkzeug generate_password_hash
}
```
Index: `email` unique. Managed by `app/models/users.py`. No roles/teams —
this app is designed for a single user (or a small number of independent
users, each seeing only their own... actually **note**: aspects/metrics/etc.
are *not* currently scoped by user_id — see "Known gaps" below).

### `life_aspects`

```
{
  _id: ObjectId,
  name: str,
  slug: str,                        # unique, derived from name, deduped with -2/-3/...
  color_light: str, color_dark: str,  # hex, assigned via app/colors.py::slot_for_order
  icon: str,
  order: int,                       # insertion order, drives display + color slot
  transaction_config: {              # or null — quick-add log is opt-in per aspect
    amount_label: str,               # e.g. "Amount", "Hours"
    categories: [str, ...]           # user-defined, e.g. ["Expenditure", "Savings", ...]
  } | null,
}
```
Index: `slug` unique. Managed by `app/models/life_aspects.py`.
`delete_aspect` cascades: deletes all `metrics` under it (and their
`entries`), all `transactions` under it, then the aspect itself.

### `metrics`

```
{
  _id: ObjectId,
  aspect_id: ObjectId,        # -> life_aspects
  name: str,
  type: "number" | "boolean" | "rating",
  cadence: "daily" | "monthly",
  unit: str,
  target: { value: float, direction: "at_least" | "at_most" } | null,
  active: bool,                # soft-delete flag; false = archived
  order: int,                  # insertion order within the aspect; [0] is the dashboard "headline" metric
}
```
No index beyond the default `_id`. Managed by `app/models/metrics.py`.
`archive_metric`/`reactivate_metric` toggle `active` rather than deleting,
so historical `entries` stay intact and queryable even after a metric is
retired.

### `entries`

```
{
  _id: ObjectId,
  metric_id: ObjectId,   # -> metrics
  date: datetime,        # always midnight — day_key() for daily, month_key() for monthly
  value: float | int | bool,
  note: str,
  created_at: datetime,
}
```
Index: `(metric_id, date)` **unique** — this is what makes
`upsert_entry` idempotent per day/month. Managed by
`app/models/entries.py`. **Always** pass dates through `day_key()` or
`month_key()` before querying or writing this collection; a raw
`datetime.now()` with a nonzero time component will violate the assumption
every other query in this collection relies on (exact-match on a
midnight-normalized date) and silently create duplicate/unfindable entries.

### `transactions`

```
{
  _id: ObjectId,
  aspect_id: ObjectId,   # -> life_aspects (only meaningful if that aspect has transaction_config set)
  date: datetime,        # day_key()-normalized, same convention as entries
  name: str,
  description: str,
  amount: float,
  category: str,          # must match one of aspect.transaction_config.categories
  created_at: datetime,
}
```
Index: `(aspect_id, date)` (non-unique — many transactions per day).
Managed by `app/models/transactions.py`. `category` is free text at the
DB level; the only place it's validated against the aspect's configured
category list is `daily.save_today` (server-side) — see
`app/blueprints/daily/routes.py`. If you write transactions from a new code
path, validate the category there too, or reports in
`totals_by_category` will silently ignore mismatched categories (that
function only sums into the categories passed to it).

### `reviews`

```
{
  _id: ObjectId,
  period_type: "monthly",             # only value in use; quarterly/annual are out of scope for v1 (see project-prompt-v1.0.0.md)
  period_start: datetime,              # month_key()-normalized, first of the month
  aspect_reflections: [
    { aspect_id: ObjectId, highlights: str, lowlights: str, focus_next: str }, ...
  ],
  completed_at: datetime,              # set via $currentDate on every save
}
```
Index: `(period_type, period_start)` unique. Managed by
`app/models/reviews.py`. One document per calendar month, upserted on every
save (`reviews.review` POST handler) — editing a past review overwrites the
whole `aspect_reflections` array, it isn't append-only.

## Entity relationships

```
users            (independent — not currently linked to other collections)

life_aspects
  └─ metrics            (aspect_id)
       └─ entries        (metric_id)
  └─ transactions        (aspect_id)

reviews  (aspect_reflections[].aspect_id references life_aspects, but reviews
          are not deleted/updated when an aspect is deleted — see gaps below)
```

## Migrations

There's no migration framework (no Alembic-for-Mongo equivalent) — schema
changes are one-off Python scripts at the repo root, run manually, and kept
around for anyone upgrading an older database:

- **`migrate_transactions.py`** — earliest version tracked "Finances" via
  four separate `metrics` documents (Expenditure, Savings, Investments,
  Current debt). This script archives those four metrics
  (`active: false`, preserving their `entries` history) and turns on the
  original boolean `tracks_transactions` flag + a hardcoded Finances
  category set. Superseded by the next script but kept for anyone
  upgrading directly from that era.
- **`migrate_configurable_transactions.py`** — converts the old boolean
  `tracks_transactions` flag into the current `transaction_config` object
  (custom `amount_label` + `categories` per aspect, not just Finances), and
  re-cases any existing `transactions.category` values to match the
  configured category strings exactly (the old scheme stored lowercase
  category keys, which would otherwise silently fall out of
  `totals_by_category` rollups since that function keys by exact string
  match). Safe to run more than once — it only touches aspects still
  missing `transaction_config`.

**If you change a document shape**: add a new one-off script following this
pattern (idempotent, prints what it did, reads `MONGO_URI`/`MONGO_DBNAME`
from env same as `seed.py`) rather than writing an in-place field rename in
model code — old data needs an explicit, run-once path forward, not a
runtime shim.

## Known gaps (be aware, don't silently "fix" without asking)

- `life_aspects`/`metrics`/`transactions`/`reviews` are **not** scoped by
  `user_id` — in a multi-user deployment, every logged-in user currently
  sees the same global data. This matches the "personal, single-user app"
  scope in `project-prompt-v1.0.0.md`; don't assume this is a bug to fix
  without checking scope with the user first.
- Deleting a `life_aspects` doc does not clean up references to it inside
  historical `reviews.aspect_reflections` — those entries become orphaned
  (harmless to read, since the template just won't find a matching aspect
  to render against, but worth knowing if you touch review rendering).

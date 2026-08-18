# Extending Second Brain

This page is a recipe list for common changes, plus pointers to what
already exists so you extend rather than duplicate it. Written for both a
human contributor and an AI agent picking up a task cold.

## Before you start

1. Read [`architecture.md`](architecture.md) for the request-flow shape
   (route → model(s) → template) — new code should follow it, not introduce
   a service layer, a query builder, or a class-based model for a single
   feature.
2. Check whether the thing you want already exists as **user
   configuration** rather than code: new life aspects, new metrics, and
   enabling/customizing the quick-add transaction log are all done from the
   Settings UI, no code change required (see
   [`README.md`](README.md#project-summary)).
3. If it's a genuine schema change, read
   [`database.md#migrations`](database.md#migrations) first — this repo's
   convention is a one-off idempotent script at the repo root, not an
   in-place silent field rename.

## Recipe: add a new blueprint (top-level feature/page)

1. `app/blueprints/<name>/__init__.py` (empty) and `routes.py` defining
   `Blueprint("<name>", __name__, url_prefix="/...")`.
2. Register it in `create_app()` (`app/__init__.py`) alongside the existing
   five.
3. Add `@login_required` to every view except ones that must be reachable
   logged-out (mirror `auth.login`).
4. Templates go in `app/templates/<name>/`, extending `base.html`.
5. Add a nav link in `base.html` if it should be reachable from the top nav.
6. Add `tests/test_<name>.py` using `logged_in_client`/`db` fixtures — see
   [`testing.md`](testing.md).

## Recipe: add a new model / collection

1. New file `app/models/<name>.py`, functions taking `db` first, matching
   the style of existing modules (return raw dicts, take string or
   `ObjectId` ids, one Mongo op per function where reasonable).
2. Add any indexes to `app/db.py::ensure_indexes` — this is the only place
   indexes are declared, and it runs on every `create_app()` including in
   tests.
3. If the new collection hangs off `life_aspects` (most things do), decide
   now whether `life_aspects.delete_aspect` should cascade-delete it —
   if yes, add that cleanup there (see how it already handles `metrics`,
   `entries`, `transactions`).
4. Document the shape in [`database.md`](database.md) (new `###` section)
   and the entity-relationship diagram there.

## Recipe: extend the quick-add transaction log

This is the most recently developed feature (see the uncommitted/WIP state
around `app/models/transactions.py`, `migrate_configurable_transactions.py`,
`tests/test_transaction_config.py`). Its contract spans four files that
must stay in sync:

- `app/models/transactions.py` — data access + `totals_by_category`.
- `app/blueprints/daily/routes.py` — renders the day's transactions and
  parses the staged `txn_<aspect_id>_<i>_<field>` fields on POST
  (`save_today`); validates `category` against
  `aspect.transaction_config.categories`.
- `app/static/js/transactions.js` — client-side staging; produces the exact
  field-naming scheme `save_today` parses (see
  [`frontend.md#transaction-quick-add-js`](frontend.md#transaction-quick-add-js)).
- `app/blueprints/reviews/routes.py` — rolls transactions up into
  this-month/last-month category totals for the monthly review.

If you add a field to a transaction (e.g. tags, currency), you need to
touch all four, plus `settings/routes.py::_parse_transaction_config` if the
new field is aspect-level config rather than per-transaction data, plus a
migration script if existing data needs backfilling.

## Recipe: add a new metric type or cadence

`METRIC_TYPES = ("number", "boolean", "rating")` and
`CADENCES = ("daily", "weekly", "monthly")` in `app/models/metrics.py` are
the only places these are enumerated as constants, but the *rendering* of
each type/cadence is hardcoded per call site in templates and routes — there
's no single dispatch table, so grep for the existing enum values
(`"boolean"`, `"rating"`, `"weekly"`) to find every place before adding a
new one. Call sites as of the `weekly` cadence addition:

- `app/blueprints/daily/routes.py::save_today`/`today` — parses/renders
  `metric_<id>` only for `cadence="daily"` metrics; a different `type`
  changes the form-field parsing (checkbox for boolean, int for rating,
  float otherwise) but not which cadence shows up here.
- `app/templates/daily/today.html` — renders a different input widget per
  `type`.
- `app/blueprints/reviews/routes.py::review`/`review_form.html` — the
  monthly review. `cadence == "monthly"` metrics get an input field;
  `cadence == "weekly"` metrics are explicitly skipped (`continue`) so they
  never enter the per-metric chart/averages either; everything else
  (`daily`) only gets the averaged summary.
- `app/blueprints/reviews/routes.py::weekly_review`/
  `weekly_review_form.html` — the weekly review, added alongside the
  `weekly` cadence. `cadence == "weekly"` metrics get an input field here
  and *only* here.
- `app/blueprints/dashboard/routes.py::home`/`aspect_detail` — both filter
  out `cadence == "weekly"` metrics (headline selection and per-metric
  charts respectively) so a weekly metric never appears on the dashboard.
- `app/analytics.py::status_for_metric` — only meaningful for numeric
  values with a `target`; extend the `isinstance` check if a new type
  should also support targets.

**If you add a new cadence**, decide up front whether it should be globally
visible (like `daily`/`monthly`, which show up in Today/dashboard/monthly
review) or deliberately siloed to one surface (like `weekly`, which is
invisible everywhere except its own review page) — then filter it out of
every *other* call site explicitly, the way `weekly` is filtered out of
`daily.today`, `dashboard.home`/`aspect_detail`, and
`reviews.review`. Missing one of these filters is the easy way to leak a
metric onto a page it shouldn't appear on.

## Recipe: schema/migration change

Follow the existing pattern in `migrate_configurable_transactions.py`:
- Read `MONGO_URI`/`MONGO_DBNAME` from env the same way `seed.py` does.
- Make it idempotent — safe to run multiple times (query for docs still in
  the old shape, e.g. `{"new_field": {"$exists": False}}`).
- Print what it did; don't silently no-op.
- Don't delete old data — archive/rename fields instead (see how
  `migrate_transactions.py` archives old metrics via `active: false` rather
  than deleting them, preserving `entries` history).
- Update `README.md`'s "Local setup" step 4 if the new script should run
  during onboarding for pre-existing databases.

## Things AI agents specifically should double-check before changing

- **Don't assume multi-user data isolation exists.** Aspects/metrics/
  transactions/reviews are global, not scoped by `user_id` (see
  [`database.md#known-gaps`](database.md#known-gaps)). If a task implies
  adding user-scoping, confirm that's actually in scope before doing it —
  it's a deliberate simplification for v1, not an oversight, per
  `project-prompt-v1.0.0.md`.
- **Don't add a frontend build step** (bundler, npm, TS) to solve a styling
  or JS problem — this app deliberately has none; work within
  CDN-Tailwind + vanilla JS, or raise the tradeoff with the user first.
- **Don't invent an ORM/service layer** for a single new feature — routes
  calling model functions directly is the established pattern throughout,
  even for fairly involved logic (see `reviews.review`'s POST handler).
- **Keep `app/colors.py` (Python) and the CSS variables in `base.html` in
  sync** if you touch either — see
  [`frontend.md#theming`](frontend.md#theming).
- Out-of-scope for v1 per `project-prompt-v1.0.0.md`: quarterly/bi-annual/
  annual reviews, multi-year comparisons, reminders, the radar
  "balance-across-aspects" chart. Don't build toward these unless asked.

# Frontend

No frontend build step: Tailwind and Chart.js are both loaded from CDN
`<script>` tags in `app/templates/base.html`, and the only JS is two small
hand-written files under `app/static/js/`. There's no `package.json`, no
bundler, no framework.

## Templates (`app/templates/`)

Server-rendered Jinja2, one subdirectory per blueprint plus `base.html`:

```
templates/
  base.html                    # layout: nav, flash messages, CDN script tags, CSS variables
  auth/login.html
  daily/today.html             # metric inputs + quick-add transaction UI + date picker
  dashboard/home.html          # per-aspect summary cards + sparklines
  dashboard/aspect_detail.html # per-metric charts, range-filterable
  reviews/history.html         # current month (+ current week) highlighted, past months below
  reviews/review_form.html     # monthly review
  reviews/weekly_review_form.html # weekly review — no charts, weekly-cadence metric inputs only
  settings/aspects.html        # aspect CRUD + transaction_config form
  settings/metrics.html        # metric CRUD (incl. inline edit), archive/reactivate
```

Every page-level template `{% extends "base.html" %}` and fills
`{% block title %}`/`{% block content %}`. `base.html` also exposes a
`{% block head %}` for page-specific `<head>` additions if ever needed.

### Theming

`base.html` defines CSS custom properties (`--surface`, `--page`,
`--ink-primary`, `--ink-secondary`, `--ink-muted`, `--gridline`,
`--baseline`, `--border`) on `:root`, redefined under
`@media (prefers-color-scheme: dark)`. These mirror the `CHROME` tokens in
`app/colors.py` — **keep the two in sync** if you change one; there's no
single source of truth linking them (the Python side is documentation of
intent, the CSS is what actually renders). Templates use these tokens via
inline `style="color: var(--ink-secondary)"` rather than Tailwind's own
dark: classes, since Tailwind here has no config file to define custom
colors in.

Aspect-specific color (`aspect.color_light` / `aspect.color_dark`) is
injected directly into template output as a hex string wherever an
aspect's brand color is needed (dots, buttons, accent-color on inputs) —
see `daily/today.html` and `dashboard/home.html` for the pattern. Only
`color_light` is used directly in most places since CSS custom properties
handle the light/dark swap for chrome; `color_dark` is passed through to
JS for canvas-based charts, which can't use CSS variables directly (see
below).

### CSRF

Every POST `<form>` includes:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```
`CSRFProtect` is enabled globally (`app/__init__.py`) — a new form missing
this will 400 on submit. Tests disable CSRF via
`WTF_CSRF_ENABLED: False` in `config_overrides` (see
[`testing.md`](testing.md)), so a missing token won't be caught by tests
unless you specifically re-enable CSRF for that test.

### Never nest a `<form>` inside another `<form>`

`daily/today.html` wraps the *entire* page (every metric input, every
transaction-staging block, and the "Save today's entries" button) in one
`<form>`. Each transaction's delete "×" needs to POST somewhere else
(`daily.delete_transaction`), and it used to do that with its own nested
`<form>` — which is invalid HTML. Per the HTML parsing spec, a browser
silently *ignores* a `<form>` open tag encountered while already inside a
form, but its matching `</form>` still closes the real outer form. The bug
this caused: the page rendered fine and "Save today's entries" worked right
up until the first transaction existed — then the outer form was silently
truncated at that transaction's delete button, and everything after it
(including the Save button, and that aspect's own "+" add-transaction
fields, which sit later in the same block) fell outside any form and
stopped doing anything on click. It looked like intermittent JS breakage;
it was actually a parser artifact with no error in the console.

**The fix, and the pattern to reuse**: give the button its own
`formaction`/`formmethod` attributes instead of wrapping it in a form —
```html
<button type="submit" formaction="{{ url_for('daily.delete_transaction', transaction_id=txn._id) }}"
        formmethod="post" formnovalidate>&times;</button>
```
This submits the *entire* enclosing form (so it already carries the shared
`csrf_token`/`date` hidden fields — no need to duplicate them) to a
different endpoint than the form's default action. Reach for this any time
a page needs more than one POST target inside what should be a single form;
never reach for a nested `<form>`. A quick regression check for this class
of bug: the rendered page should contain exactly one `<form` inside
`<main>` (see `tests/test_daily.py::test_transaction_delete_control_does_not_nest_a_form`).

## Static JS (`app/static/js/`)

Two independent, framework-free files, each loaded only on the pages that
need them (`<script src="{{ url_for('static', filename='js/...') }}">` at
the bottom of the relevant template — not globally in `base.html`).

### `charts.js` — Chart.js wrapper {#charts}

Exposes a small `SecondBrain` global (see `dashboard/home.html` and
`dashboard/aspect_detail.html` for call sites) used to draw sparklines/line
charts from the JSON series produced by `app/analytics.py::sparkline_series`
or built inline in `dashboard.aspect_detail`. Series are passed into the
template as Python lists of `{date, value}` dicts and serialized with
Jinja's `| tojson` filter directly into a `<script>` block — no separate
API/fetch call, the chart data is rendered server-side into the page.

### `transactions.js` — quick-add transaction staging {#transaction-quick-add-js}

Powers the "add a transaction" UI on `daily/today.html` for any aspect with
`transaction_config` set. This is a client-side-only staging mechanism —
**nothing is sent to the server until the whole "Save today's entries"
form is submitted.**

How it works (`app/static/js/transactions.js`):
1. For each `[data-txn-form]` block (one per transaction-enabled aspect,
   keyed by `data-aspect-id`), it reads the Name/Description/Amount/Category
   inputs when "+" is clicked (or Enter is pressed in a field).
2. It injects hidden inputs into the enclosing `<form>` named
   `txn_<aspectId>_<index>_name`, `..._description`, `..._amount`,
   `..._category`, and bumps a `txn_count_<aspectId>` hidden input — this
   naming scheme is exactly what
   `app/blueprints/daily/routes.py::save_today` expects when parsing the
   POST body (`prefix = f"txn_{aspect['_id']}_{i}_"`, looped
   `range(count)`). **If you change one side of this contract (field
   naming, the count field), you must change the other.**
3. It renders a small removable "staged" row in the UI; clicking the "×"
   removes the row *and* disables (not removes) its hidden inputs
   (`el.disabled = true`) so they're excluded from the form submission
   without disturbing the index numbering of the other staged rows.

There's no client-side validation beyond requiring a non-empty name and
amount before staging a row — category correctness and numeric parsing are
enforced server-side in `save_today`.

### Today page date navigation

`daily/today.html` offers three ways to change which day you're viewing:
prev/next arrows (±1 day), and an `<input type="date">` picker that jumps
straight to any date via `onchange="window.location.href = ... + this.value"`
(inline, no separate JS file — it's a one-liner). All three are just plain
navigation to `/today?date=YYYY-MM-DD`; there's no client-side state, so
editing a past day's values works exactly like editing today's — the
pre-filled form is populated server-side from `entries_for_metrics_on` for
whatever `the_date` the route resolved (see `daily.today`/`_parse_date`).

## Adding a new page

1. Add a route in the relevant blueprint (or a new blueprint — see
   [`extending.md`](extending.md)).
2. Add a template under `app/templates/<blueprint>/`, extending
   `base.html`.
3. Reuse the `--ink-*`/`--surface`/`--border` CSS variables and the
   `sb-surface` class for card-like containers, rather than introducing new
   ad hoc colors — this keeps light/dark mode consistent for free.
4. If the page needs its own aspect-colored UI, pass `color_light`/
   `color_dark` through from the route the same way existing templates do;
   don't hardcode hex values in a template.
5. Add a nav link in `base.html` if it's a top-level page.

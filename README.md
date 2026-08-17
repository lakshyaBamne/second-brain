# Second Brain — v1.0.0

Personal growth tracker: daily entries roll up into monthly reviews, per life
aspect. See `project-prompt-v1.0.0.md` for the original goals and the design
doc this was built from (Flask + MongoDB + Tailwind, lean MVP scoped to a
single life aspect — Finances — end to end).

## Stack

Flask, MongoDB, Tailwind CSS (CDN), Chart.js (CDN). No JS framework, no
frontend build step.

## Local setup

1. **MongoDB** — a local MongoDB 8.3.8 is already set up at
   `C:\Users\<you>\mongodb\` (portable, no install/admin rights used). Start it
   any time by double-clicking `start-mongodb.bat` in this repo (or running it
   from a terminal) — it listens on `127.0.0.1:27017` and stops with Ctrl+C.
   Data lives in `C:\Users\<you>\mongodb\data\db`. Alternatively, use a free
   [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster (M0 tier)
   instead — see below.
2. **Python env**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```
3. **Config** — copy `.env.example` to `.env` and fill in `MONGO_URI` (and a
   random `SECRET_KEY`).
4. **Seed data** — creates your login plus the Finances aspect (transaction
   tracking enabled) and its one manual metric, In-hand money:
   ```
   python seed.py
   ```
   If you're upgrading a database seeded before the transaction-log rework,
   run `python migrate_transactions.py` instead/first — it flips on
   transaction tracking for Finances and archives (not deletes) the old
   Expenditures/Savings/Investments/Current debt metrics, keeping their
   history intact.
5. **Run**
   ```
   python wsgi.py
   ```
   Visit `http://127.0.0.1:5000` and log in with the credentials from step 4.

## Tests

```
pytest
```

Tests run against an in-memory MongoDB (`mongomock`), so no database
connection is needed to run them.

## Adding more life aspects / metrics

Settings → Life aspects / Metrics — no code changes needed. New aspects are
assigned the next color in a validated, colorblind-safe palette automatically.

Check "Enable a quick-add log" when adding an aspect (or later, via each
aspect's "Quick-add log settings") to give it its own add-a-transaction
(name/description/amount/category) flow on the Today page, collated by
category in monthly reviews. Both the categories and what the amount
represents are fully custom per aspect — e.g. Finances uses
Expenditure/Savings/Investments/Debt in currency, a Health aspect might use
Gym/Sports/Others in hours.

## Deploying (when ready)

- App: [Render](https://render.com) or [Railway](https://railway.com) — point
  at this repo, set the same env vars as `.env`.
- Database: MongoDB Atlas free tier.

## What's not in v1.0.0

Quarterly/bi-annual/annual review workflows, multi-year comparisons,
reminders, and the radar "balance across aspects" chart are intentionally
deferred — see the design doc's scope section.

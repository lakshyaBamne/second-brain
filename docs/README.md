# Second Brain — Documentation

This is the documentation set for Second Brain, a personal growth tracker
(Flask + MongoDB + server-rendered Jinja2, no frontend build step). It's
written for two audiences at once: a developer ramping up on the codebase,
and an AI agent that needs enough context to make a correct change without
re-reading every file first.

Start with whichever page matches what you're about to touch:

| Page | Read this when you're working on... |
|---|---|
| [`architecture.md`](architecture.md) | Getting oriented: request flow, directory layout, how pieces fit together |
| [`backend.md`](backend.md) | Blueprints, models, `app/analytics.py`, `app/colors.py`, the app factory |
| [`database.md`](database.md) | MongoDB collections, document shapes, indexes, migrations |
| [`frontend.md`](frontend.md) | Jinja2 templates, Tailwind, Chart.js, the vanilla-JS in `app/static/js/` |
| [`testing.md`](testing.md) | Writing or running tests, the fixture chain in `tests/conftest.py` |
| [`extending.md`](extending.md) | Adding a feature (a new blueprint, a new per-aspect capability, a schema change) |

`../CLAUDE.md` is the short version of this (commands + a condensed
architecture summary) meant to fit in an AI agent's system context on every
turn. This `docs/` tree is the long version — reach for it when `CLAUDE.md`
doesn't have enough detail, and when either one goes stale, fix both.

## Project summary

Daily entries roll up into monthly reviews, organized per user-defined "life
aspect" (Finances, Health, ...). Each aspect can have:

- **Metrics** — number/boolean/rating values logged daily or monthly (e.g.
  "Slept well?", "In-hand money").
- **A quick-add transaction log** (optional, per aspect) — a free-form
  name/description/amount/category ledger, e.g. Finances tracks
  Expenditure/Savings/Investments/Debt in currency; a Health aspect could
  track Gym/Sports/Others in hours instead.

Everything — aspects, metrics, whether the transaction log is on, its
categories — is user-configurable via the Settings UI. No code changes are
needed to add a new life aspect or metric; see
[`extending.md`](extending.md) for what *does* need code.

See `../project-prompt-v1.0.0.md` for the original product design doc and
scope decisions, and `../README.md` for local setup and run instructions.

## Conventions used across this doc set

- File paths are relative to the repo root unless stated otherwise.
- "Route" and "view" are used interchangeably for Flask view functions.
- Mongo documents are described as `{field: type, ...}`; `ObjectId` fields
  are written as `<ref:collection>` when they reference another collection.
- Code samples are trimmed for relevance — check the referenced file for the
  full, current version rather than trusting a doc snippet verbatim.

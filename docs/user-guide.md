# Using Second Brain — a guide for the person actually using the app

This page is for **you, the user**, not for a developer or AI agent working
on the codebase (that's what the rest of `docs/` is for — see
[`README.md`](README.md)). It explains what each part of the app is for and
how to get the most out of it.

## The core idea

Second Brain is built around one loop: **log a little every day → review
what it adds up to on a schedule.** Everything in the app supports that
loop:

```
Life aspect (Health, Finances, ...)
  └─ Metrics you log daily / weekly / monthly
  └─ (optionally) a quick-add transaction log
       ↓
  Today page (daily logging)
       ↓
  Weekly review  ──┐
  Monthly review ──┴─→ reflection + trend charts
       ↓
  Dashboard (always-on summary, any time)
```

You don't have to use every piece — a single life aspect with one daily
metric is a complete, useful setup. Add more structure only when you feel
the lack of it.

## 1. Life aspects — your top-level categories

**Settings → Life aspects.** A life aspect is a category of your life you
want to track separately — Health, Finances, Career, Relationships,
whatever grouping makes sense to you. Each one gets:

- Its own color (assigned automatically, in order, from a fixed
  colorblind-safe palette — you don't pick it).
- Its own set of metrics.
- Optionally, its own **quick-add transaction log** (see below).

You can rename an aspect any time. **Deleting an aspect deletes everything
under it** — its metrics, every logged value for those metrics, and every
transaction — so treat delete as permanent. If you just want to stop
tracking something but keep the history, archive the metric instead (see
below) rather than deleting the aspect.

There's no fixed list of aspects — add as many or as few as make sense.
Two or three focused aspects tend to work better than ten shallow ones,
since each one adds a review section you're committing to filling in.

## 2. Metrics — the things you actually track

**Settings → Metrics.** A metric is one trackable value under an aspect.
When you add one, you choose:

| Field | Options | What it controls |
|---|---|---|
| **Type** | Number / Boolean / Rating | Number → a plain numeric input. Boolean → a single checkbox ("did this happen?"). Rating → a 1–5 scale (mood, energy, quality — anything subjective). |
| **Cadence** | Daily / Weekly / Monthly | *Where* you log it and how often — see below. |
| **Unit** | free text, optional | Just a label shown next to the value (e.g. "hours", "kg", "currency"). Purely cosmetic. |
| **Target** | a number + "at least"/"at most", optional | Compared against your *latest* entry to show a green "On track" or amber "Needs attention" badge on the dashboard and aspect page. Only meaningful for Number metrics. |

### Choosing a cadence

This is the one choice that actually changes *where* a metric shows up, so
it's worth getting right:

- **Daily** — logged on the **Today page**, one value per day. Use this for
  anything you can realistically note every day: sleep hours, whether you
  worked out, water intake, mood.
- **Weekly** — logged on that week's **weekly review** page, one value per
  week. Deliberately **invisible everywhere else** — not on Today, not on
  the dashboard, not in the monthly review. Use this for things that are
  either too noisy to mean anything daily or too much friction to log every
  day, but where "once a month" loses too much signal: a weekly weigh-in,
  a weekly energy/burnout self-rating, hours spent on a side project.
- **Monthly** — logged on the **monthly review** page, one value per month.
  Use this for slow-moving numbers you only realistically check once a
  month anyway: net worth, resting heart rate, a subscription count.

If you're not sure, start **daily** — you can always change a metric's
cadence later from its Edit panel in Settings without losing any history
(existing logged values stay where they are; only new entries follow the
new cadence).

> **A quirk worth knowing**: Boolean and Rating metric *types* only get
> their proper checkbox/1–5 widget on the **Today page**. On the weekly and
> monthly review pages, every metric input — regardless of type — is a
> plain number box. So a Boolean or Rating metric only really makes sense
> on a **daily** cadence; if you want a weekly or monthly metric, stick to
> **Number** type so the input matches what you're entering.

### Editing, archiving, and reactivating metrics

Every metric in Settings → Metrics has an **Edit** disclosure — click it to
change the name, type, cadence, unit, or target in place, then Save
changes. This is the only way to fix a typo'd name or adjust a target
without losing history (which is what would happen if you deleted and
re-added it).

If you stop caring about a metric, **Archive** it rather than deleting —
archiving hides it from Today/reviews/dashboard but keeps every value you
ever logged, and you can Reactivate it later with full history intact.
There's no "delete a metric" action for exactly this reason.

## 3. Quick-add transaction log — for anything with a running list

**Settings → Life aspects → "Enable a quick-add log"** (or edit it later
per-aspect). This is a different shape of tracking than metrics: instead of
one value per period, it's a free-form ledger of name/description/
amount/category entries you add as they happen. Enable it when you have
several distinct *things* to log per day rather than one number — Finances
is the obvious case (Expenditure/Savings/Investments/Debt), but it works
for anything with a natural "category" split: a Health aspect logging Gym/
Sports/Others in hours, a Learning aspect logging Reading/Courses/Practice
in minutes.

You define the **categories** and what the amount represents (the "amount
label" — "Amount", "Hours", "Minutes", whatever fits) once per aspect; both
are fully custom, not a fixed enum.

On the Today page, add entries with the **+** button — this only stages
them locally in the page; nothing is saved until you click **Save today's
entries**. The monthly review rolls transactions up into this-month-vs-
last-month totals per category automatically; there's no separate
transaction cadence to think about.

## 4. Today page — your daily habit

This is the page you should have open most days. For each aspect with
daily metrics and/or a transaction log, it shows one form combining both.

- **Navigating days**: use the ← / → arrows to move one day at a time, or
  the date field next to them to jump straight to any date — past or
  future. Editing a past day's values works exactly like editing today's:
  the form pre-fills with whatever was already logged for that day, and
  saving overwrites that day's value rather than creating a duplicate. This
  is the right way to fix a mistake or backfill a day you missed — there's
  no separate "edit" mode, you just navigate there and change it.
- **"Save today's entries"** saves *everything currently on the page* in
  one action — every metric value you've touched and every staged
  transaction — for whichever day you're viewing. It's safe to save
  repeatedly; unfilled fields are simply left as they were.
- Any edit you make here is reflected immediately, everywhere it's relevant
  (dashboard cards, sparklines, monthly averages) — there's no caching or
  delay, because those pages always compute from the current data.

## 5. Dashboard — the always-on overview

**Dashboard** (home page) shows one card per life aspect:

- If the aspect has metrics, the card shows its **headline metric** — the
  oldest active (non-archived) metric on that aspect, skipping any
  weekly-cadence ones since they're not meant to surface here — with its
  latest value, a 30-day sparkline, and an On track/Needs attention badge
  if that metric has a target. There's no way to manually pick the
  headline metric; if you want a specific one featured, it needs to be the
  first non-weekly metric you added (or the only one left active).
- If the aspect has no metrics but does have a transaction log, the card
  shows the last-30-days total instead.

Click into a card for the **aspect detail page**: a chart per metric (again
skipping weekly-cadence ones), a category breakdown of the transaction log
if enabled, and a range switcher (Week / Month / Quarter / All time) to
zoom the charts in or out.

## 6. Reviews — where logging turns into reflection

**Reviews** in the nav takes you to the review history: the **current
month** always appears first as its own highlighted card, with earlier
months (any month you've saved at least one review for) listed below in
reverse-chronological order. Each month's card holds **5 sub-cards**: Week
1 through Week 4, and Month. The week you're currently in is marked
"Current"; any period you've already saved shows "Completed" so you can see
at a glance what's outstanding.

Note that a month is always split into exactly 4 weeks — days 1–7, 8–14,
15–21, and 22-through-end — not literal Monday–Sunday calendar weeks. This
keeps every month's review structure identical regardless of what weekday
it starts on.

- **Weekly review** (a Week card): reflection prompts (what went well /
  what needs improvement / focus for next week) per aspect, plus an input
  for each **weekly-cadence** metric on that aspect. Deliberately
  lightweight — no charts, no transaction rollup. This is the *only* place
  weekly metrics are entered or shown.
- **Monthly review** (the Month card): the same three reflection prompts
  per aspect, plus an input for each **monthly-cadence** metric, plus a
  trend chart comparing this month vs. last month for every daily and
  monthly metric on that aspect, plus (if enabled) a category-by-category
  breakdown of the transaction log for the month.

Both kinds of review can be re-opened and re-saved at any time — saving
overwrites that period's reflections rather than appending, so treat it as
"the current state of this review," not a running log.

## Putting it together: a suggested workflow

1. **Set up once**: create a life aspect per area of your life you want
   visibility into. Add a couple of daily metrics per aspect to start —
   resist the urge to add ten metrics on day one, since you have to
   actually fill them in every day for them to be worth anything.
2. **Log daily**: open Today, fill in whatever applies, hit Save. Takes
   under a minute once metrics are dialed in.
3. **Add weekly metrics later, deliberately**, once you notice something
   daily logging doesn't capture well (mood trends, a weekly check-in
   number) — not by default.
4. **Do the weekly review** for a quick pulse check with minimal writing.
5. **Do the monthly review** for the fuller picture — this is where the
   trend charts and transaction rollups make patterns visible that daily
   logging alone won't show you.
6. **Check the Dashboard** any time you want a snapshot without doing a
   full review — it's read-only and always current.
7. **Prune over time**: archive metrics that stopped being useful,
   re-target or re-cadence ones that need adjusting via Edit, rather than
   deleting and losing the history that makes the trend charts meaningful
   in the first place.

## FAQ / troubleshooting

**I logged the wrong value for a past day — how do I fix it?**
Go to Today, use the date picker (or arrows) to navigate to that day, edit
the value, click Save. It overwrites, it doesn't duplicate.

**I deleted a transaction by mistake.**
There's currently no undo for a deleted transaction — you'll need to
re-add it via the Today page for that day.

**A metric I archived is gone from Today/Dashboard/Reviews — did I lose its
history?**
No — archiving only hides it going forward. Reactivate it from Settings →
Metrics and every previously logged value is still there.

**Why doesn't my weekly metric show up on the Dashboard or in the monthly
review?**
That's intentional, not a bug — see [Choosing a cadence](#choosing-a-cadence)
above. Weekly-cadence metrics only ever appear on their own weekly review
page.

**Can I track quarterly or yearly reviews?**
Not in this version — see the project's design doc for what's intentionally
out of scope for now.

# Orbitly — Activation & Retention Analysis

**Question:** why do so many people try Orbitly but fail to become engaged, paying customers?

Orbitly is a fictional B2B SaaS product that sells marketing-analytics dashboards through a 14-day self-serve trial. This project uses a seeded synthetic dataset to practise the kind of analysis a Growth Analyst or Business Analyst would deliver: map the funnel, test retention hypotheses, diagnose friction, read experiment results and rank the next tests.

> **Data note:** all records are generated. These are calculated findings about the simulation, not claims about a real company.

## What I found

- In the user-level funnel, **3,842 of 20,644 non-bot, non-invited-marked signups reached the observed `report_shared` event within 14 days (18.6%)**. The event is deliberately under-recorded for a small ad-blocker group, so this is an observed activation rate, not necessarily the true rate.
- The largest **absolute** funnel loss is workspace creation → data-source connection: **6,229 users**, or **39.8% of those who created a workspace**. Among users who tried to connect but never succeeded, **49.8% stopped after one failed attempt**. `unknown_error` and `oauth_denied` represent **56.4% of the deduplicated connection-failure events**.
- `data_source_connected` has the strongest channel-adjusted association with 90-day account retention among the early actions tested (**+18.4 percentage points** for doers vs. non-doers, adjusted within acquisition channel). This is an observational association, not proof that the action causes retention. `report_shared` remains the product-defined activation event, but ad-blocking can hide some of those events.
- Time-to-value is associated with retention, but the pattern isn't perfectly monotonic: accounts with an observed share within 24 hours had **59.6%** 90-day retention; the 24–48h group was **61.6%**; the >96h group was **42.3%**. The slowest group retained less often, but these groups aren't randomized.
- Referral and organic-search accounts activate more often than paid-social accounts in this simulation. **There is no channel spend or CAC data**, so this supports further channel-quality investigation, not a budget-reallocation conclusion.
- The three synthetic experiment readouts all have approximate 95% confidence intervals that include zero. The right takeaway is **inconclusive**, not “the experiment won.”

## What I would test first

1. **Improve the connection step:** show error-specific recovery actions and a guided retry. Add a sample-data path so an integration problem doesn't end product evaluation.
2. **Fix activation measurement:** log `report_shared` server-side or add a reconciliation event, then quantify the current undercount.
3. **Test channel quality before changing spend:** compare activated accounts and CAC by channel; today's dataset has outcome quality but no acquisition economics.
4. **Run a properly powered follow-up test:** pre-register the hypothesis, primary metric, guardrails, sample size and runtime. The existing synthetic readouts don't validate any proposed lift.

## The project in one line

I built a repeatable analysis from generated event data to a ranked experiment backlog, while separating user-level product events from account-level paid and retention outcomes.

## What's in the repo

```text
orbitly-activation/
├── data_generator.py             # seeded synthetic users, events, subscriptions and experiment assignments
├── DATA_DICTIONARY.md            # table grains, fields and seeded data-quality issues
├── sql/                          # shared view + 10 analysis scripts
├── build_excel.py                # builds the RICE, ARR and experiment workbooks
├── excel/
│   ├── rice_prioritization.xlsx
│   ├── arr_scenario.xlsx
│   └── experiment_tracker.xlsx
├── dashboard/
│   ├── build_dashboard.py        # rebuilds the dashboard from SQL and workbook inputs
│   └── index.html                # generated interactive dashboard
├── docs/
│   ├── rca.md
│   ├── kpi_tree.md
│   ├── experiment_plan.md
│   └── user_stories.md
├── analysis_results.md            # current findings and limitations
├── recommendation_memo.md
├── build_project.py               # end-to-end rebuild command
└── validate_project.py            # SQL/workbook/dashboard checks
```

## Rebuild it

Requires Python 3.10+ and packages in `requirements.txt`.

```bash
python3 -m pip install -r requirements.txt
python3 build_project.py
```

The first run creates `orbitly.db`, then builds the shared event view, Excel files and dashboard. Dataset generation can take a few minutes. To recreate the seeded dataset later:

```bash
python3 build_project.py --regenerate-data
```

To run a single analysis, make sure `orbitly.db` and `v_events` exist, then run the relevant SQL file against SQLite. The dashboard is generated from the current database; charts use Plotly from a CDN, so an internet connection is needed to render it.

## Definitions and caveats

- **Product funnel:** counts user records by the required sequence of events within 14 days. The segment is `invited_by IS NULL` and `is_bot = 0`; it means “not marked as invited,” not necessarily a verified unique buying account.
- **Paid conversion and 90-day retention:** measured at account level, using the earliest eligible account user and the `subscriptions` record. These rates should not be mixed with user-level funnel counts without stating the denominator.
- **Activation event:** `report_shared` is Orbitly's defined activation event. A seeded ad-blocker issue removes about 8% of true share events from the event log, so observed activation is a lower bound.
- **Aha analysis:** retention gaps are adjusted within acquisition channel, but remain observational. They do not prove causality.
- **Experiments:** the A/B readouts are synthetic practice data. The reported confidence intervals are approximate Wald intervals; all three intervals include zero in this run.
- **ARR:** the +5 percentage-point activation scenario is a model, not realized or guaranteed revenue. It uses an assumed 45% 12-month account retention value because the dataset does not directly provide a validated 12-month revenue-survival curve.
- **Channel analysis:** there is no CAC or channel-spend table, so do not use activation rate alone to reallocate actual budget.

This project is intended to show the reasoning trail—what I counted, what I inferred, what remains uncertain and what I would test next—not to make the synthetic results look more conclusive than they are.

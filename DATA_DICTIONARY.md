# Orbitly — Data Dictionary

Synthetic data for the Activation & Retention Analytics case study.
All timestamps: UTC, **except** events before 2025-06-01 which were stored in
IST wall-time by a pre-fix instrumentation bug (add -5:30 to compare across eras).

## Tables (rows as generated: 2026-10-12)

| Table | Rows | Grain |
|---|---|---|
| users | 24000 | one row per trial user |
| accounts | 16714 | one row per company account |
| events | 1,638,311 | one row per product event |
| subscriptions | 16714 | one row per account |
| experiments | 6000 | one row per account × experiment |
| funnel_defs | 8 | the KPI contract: step -> defining event |

### users
user_id, account_id, signup_at, acquisition_channel, plan_trial, is_bot (1=bot),
invited_by (user_id of inviter, or 'external', or NULL)

### accounts
account_id, company_size_band, industry, signup_cohort_month

### events
event_id, user_id, event_name, event_at, properties (JSON string)
Key events: signup, invite_accepted, workspace_created, data_source_connect_attempted,
data_source_connect_failed (properties.error), data_source_connected, template_used,
report_created, report_viewed, report_shared, week2_active, trial_converted,
session_start, page_view.

### subscriptions
account_id, converted_at, plan (**"Pro" before 2025-01-15, "Growth" after — same tier**),
mrr, churned_at, retained_90d (1/0 for converted accounts with observable follow-up; **NULL for non-converters or cohorts without 90-day follow-up**)

### experiments
experiment_id (EXP-OAUTH, EXP-CHECKLIST, EXP-TEMPLATES), account_id,
variant (A/B), started_at

### funnel_defs
step, step_order, defining_event. `retained_90d` is DERIVED (from subscriptions),
not an event — join carefully.

## Known data-quality issues (seeded deliberately)
1. ~2% duplicate events from client retry logic (same user/event/properties, seconds apart).
2. Bot signups: is_bot=1; also detectable by behavior (hundreds of events in minutes).
3. Mixed timezones: pre-2025-06-01 event_at is IST wall-time; post-fix is UTC.
4. Plan rename: "Pro" -> "Growth" on 2025-01-15 breaks naive plan filters.
5. Ad-blocker bias: ~8% of true activated users are missing their report_shared event
   (the later account outcome may still exist, so observed activation is an undercount).
6. Invited teammates appear as signups in raw counts; separate via invited_by.

## Scenario assumptions (not facts)
Funnel probabilities, channel mix/quality, the OAuth-error story, and experiment
effects are authored scenario parameters so the analysis has something real to
find. Treat all findings as findings *about this synthetic company*.

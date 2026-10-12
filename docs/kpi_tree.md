# Orbitly KPI definitions

I would not use one funnel chart as the source of truth for every outcome. Product events happen at user level, while payment and 90-day retention are stored at account level, so the denominator needs to be written down beside each metric.

## Outcome metrics

| Metric | Current synthetic readout | Grain / definition | Owner to align with |
|---|---:|---|---|
| Observed activation | 18.6% | User-level `report_shared` within 14 days among non-bot users with `invited_by IS NULL` | Growth PM |
| Account trial-to-paid | 20.0% | Paying accounts / eligible account owners | Growth lead + Finance |
| 90-day retention | 50.6% | `retained_90d` among mature account outcomes with an observable value | Product |
| Workspace-to-connection | 60.2% of workspace creators connect | Sequential user funnel within 14 days; 9,437 / 15,666 | Product + Engineering |
| Connection failures with vague/denied errors | 56.4% | `unknown_error` + `oauth_denied` as share of deduplicated connection-failure events | Engineering |
| One-attempt abandonment | 49.8% | Among non-invited-marked users with a failed attempt who never connect | Product |

These are calculated from this seeded dataset, not company benchmarks. The activation rate is an observed rate; the generator suppresses roughly 8% of true `report_shared` events to model ad-blocker undercount.

## Early-action / retention indicators

The strongest channel-adjusted association in the current run is `data_source_connected` (+18.4 percentage points for doers vs. non-doers in 90-day retention). `report_shared` is the product-defined activation event and shows a +15.9-point adjusted association. Neither value is causal evidence.

## Measurement contracts

- Product funnel steps are user-level, sequential events within a 14-day trial window.
- For an account conversion/retention metric, count an account once, using the earliest eligible non-bot account user and its subscription outcome.
- Do not mix invited or uninvited-marked user rows with account-owner counts without stating the grain.
- Normalize pre-June-2025 event timestamps using `v_events` before comparing times.
- Treat `report_shared` as under-recorded until its server-side event capture is validated.
- Report experiment differences with uncertainty intervals. A point estimate is not a decision by itself.

## Suggested cadence if this were a live product

- Weekly: stage conversion, connection errors, abandonment and TTV by cohort/channel.
- Monthly: account conversion, activation and early retention cohorts.
- Per experiment: pre-register primary metric, guardrails, sample-size plan and decision rule before launch.

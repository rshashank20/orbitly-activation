# Orbitly analysis results

**Dataset:** seeded synthetic data, July 2024–June 2025 signup cohorts. All findings below are calculated from the generated SQLite database unless explicitly labelled as a planning assumption.

## 1. Funnel and biggest drop

The user-level funnel uses non-bot users whose `invited_by` field is null. It requires each event to occur after the preceding stage and within the 14-day trial window.

| Stage | Users | % of funnel base | Lost from prior stage | Loss as % of prior stage |
|---|---:|---:|---:|---:|
| Signup base | 20,644 | 100.0% | — | — |
| Workspace created | 15,666 | 75.9% | 4,978 | 24.1% |
| Data source connected | 9,437 | 45.7% | 6,229 | 39.8% |
| First report built | 6,778 | 32.8% | 2,659 | 28.2% |
| Report shared (observed activation) | 3,842 | 18.6% | 2,936 | 43.3% |
| Active in week 2 after share | 2,044 | 9.9% | 1,798 | 46.8% |

The largest absolute loss is **workspace → connection**. The largest proportional step loss is **share → week-2 activity**. `report_shared` is under-recorded for the seeded ad-blocker group, so activation is an observed rate.

## 2. Early actions and 90-day retention

The unit is the account. Only accounts with an observable 90-day outcome are included. Rates compare doers with non-doers, and the adjusted gap standardizes within acquisition channel.

| Early action | Accounts in base | Doers | Doer retention | Non-doer retention | Raw gap | Channel-adjusted gap |
|---|---:|---:|---:|---:|---:|---:|
| `data_source_connected` | 2,370 | 1,978 | 54.6% | 30.6% | +24.0 pp | **+18.4 pp** |
| `report_viewed` | 2,370 | 1,782 | 55.8% | 35.0% | +20.7 pp | +17.5 pp |
| `report_created` | 2,370 | 1,825 | 55.5% | 34.3% | +21.2 pp | +17.3 pp |
| `report_shared` | 2,370 | 1,570 | 56.9% | 38.4% | +18.5 pp | +15.9 pp |
| `workspace_created` | 2,370 | 2,216 | 51.9% | 31.8% | +20.1 pp | +8.0 pp |
| `template_used` | 2,370 | 730 | 55.2% | 48.6% | +6.6 pp | +5.9 pp |

`data_source_connected` is the strongest association after channel adjustment in this run. `report_shared` is still the product-defined activation event. These are observational gaps; they don't show that the action alone causes retention. The missing share-event instrumentation could also distort the comparison.

## 3. Time to value

Time to value (TTV) is signup → first **observed** `report_shared`, for mature converted accounts with that event logged.

| TTV | Accounts | Average time | 90-day retention |
|---|---:|---:|---:|
| <24h | 718 | 12.5h | 59.6% |
| 24–48h | 440 | 34.0h | 61.6% |
| 48–96h | 265 | 66.9h | 49.4% |
| >96h | 246 | 171.0h | 42.3% |

The >96h group is **17.3 percentage points** below the <24h group, but the first two buckets aren't monotonic. This is a relationship to investigate, not proof that faster activation by itself causes retention. Accounts missing an observed share event due to the seeded instrumentation issue are excluded from this TTV cut.

## 4. Connection friction

- 6,228 non-invited, non-bot workspace creators attempted a connection but never connected.
- Average attempts per workspace creator: **1.30**.
- **49.8%** of users who abandoned after a failed connection stopped after one attempt.
- Error-event mix: `unknown_error` 29.2%, `oauth_denied` 27.2%, `invalid_credentials` 14.7%, `token_expired` 14.6%, `timeout` 14.3%.
- `unknown_error` + `oauth_denied` = **56.4%** of deduplicated connection-failure events.

This supports testing clearer errors and guided recovery. It does not, by itself, prove the exact effect a UX change would have.

## 5. Acquisition-channel quality

| Channel | Share of account owners | Activation | Paid conversion | Paid among activated | Paid accounts with no observed activation |
|---|---:|---:|---:|---:|---:|
| Referral | 12.0% | 34.5% | 32.7% | 79.1% | 16.4% |
| Organic search | 21.5% | 28.0% | 26.0% | 71.8% | 22.9% |
| Content | 9.9% | 24.2% | 24.6% | 75.5% | 25.8% |
| Email | 6.4% | 21.0% | 23.2% | 78.0% | 29.5% |
| Paid search | 20.2% | 16.3% | 18.8% | 76.6% | 33.7% |
| Paid social | 30.0% | 5.2% | 9.3% | 66.3% | 63.2% |

Paid social has the lowest observed activation and paid conversion rates in this data. Since channel spend and CAC aren't included, these numbers justify an acquisition-quality investigation, not an immediate spend shift. A paid account with no observed `report_shared` event may reflect low product engagement, missing event capture, or both.

## 6. Engagement after onboarding

Among mature converted accounts, days 8–30 behavior separates retained vs. not retained only modestly:

| 90-day outcome | Accounts | Event breadth | Event count | Active days |
|---|---:|---:|---:|---:|
| Not retained | 1,170 | 2.8 | 18.2 | 4.8 |
| Retained | 1,200 | 2.9 | 20.8 | 5.3 |

The early-stage patterns are stronger than these simple engagement aggregates in this dataset, but that comparison is descriptive and could be affected by the way the synthetic outcomes were generated.

## 7. Retention activity curves

The activity curve measures whether a user had any event in a seven-day window around days 7, 14, 30, 60 and 90. Across cohorts, day-7 activity is roughly 51–54% and day-90 activity roughly 40–43%. The cohort pattern is fairly stable. There is no release/change log in the dataset, so it cannot support the claim that “nothing shipped moved retention.”

## 8. Experiment readouts

All readouts are synthetic. Approximate 95% confidence intervals for the activation difference (B − A) are:

| Experiment | A activation | B activation | Difference | Approx. 95% CI | Interpretation |
|---|---:|---:|---:|---:|---|
| EXP-CHECKLIST | 16.0% | 17.9% | +1.98 pp | −1.31 to +5.26 pp | Inconclusive |
| EXP-OAUTH | 19.0% | 21.0% | +1.96 pp | −1.54 to +5.46 pp | Inconclusive |
| EXP-TEMPLATES | 21.8% | 19.5% | −2.23 pp | −5.78 to +1.32 pp | Inconclusive |

All intervals include zero. None of these tests is a validated winner in this run. Use them as practice in interpreting point estimates and uncertainty, not as evidence for shipping.

## 9. Data-quality findings

- Bot users make up roughly 2.4–3.5% of the generated monthly signup rows.
- About 2% of events are generated as client-retry duplicates.
- Pre-June-2025 event timestamps contain the seeded IST/UTC issue; `v_events` normalizes them for analysis.
- The plan tier was renamed from `Pro` to `Growth` on 2025-01-15.
- About 8% of true `report_shared` events are suppressed in the log to model ad-blocker undercount.
- Invited users are present in raw user signups; user-level funnels and account-level outcomes must not use the same denominator interchangeably.
- Mature 90-day outcomes are only available for eligible cohorts.

## Bottom line

The clearest lead for a product change is the connection step: it has the largest absolute loss and a substantial share of connection failures have vague or denied-permission errors. The retention data show that connecting early is associated with better 90-day retention, but the evidence is observational. Channel differences deserve investigation, not a budget decision without CAC. The three generated experiments are inconclusive, so the next step is a properly designed test and better server-side activation instrumentation.

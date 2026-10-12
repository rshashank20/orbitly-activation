# Proposed experiments — activation and retention

These are proposed tests, not completed product releases. The targets below are planning assumptions to help define test size and value; they are not evidence that the changes will work.

## E1 — Guided data-source connection

- **Hypothesis:** error-specific help and a guided retry increase successful connections and 14-day observed activation.
- **Primary metric:** successful connection / workspace creators, with activation as a downstream metric.
- **Guardrails:** signup-to-workspace conversion, connection support contacts, and sample-data use versus real-data connection.
- **Planning target:** +3 percentage points; about four weeks, subject to a power calculation using current baseline and traffic.
- **Decision:** roll out only if the confidence interval and guardrails meet the pre-registered decision rule.

## E2 — Recovery nudge after a failed connection

- **Hypothesis:** a message with steps relevant to the recorded error recovers users who stop after their first failed attempt.
- **Primary metric:** successful connection within seven days of the failure.
- **Guardrails:** unsubscribe rate, complaint rate and duplicate nudges.
- **Planning target:** +3 points; about three weeks, then adjust based on the actual sample-size calculation.

## E3 — Sample-data mode

- **Hypothesis:** users can evaluate the report workflow while they are blocked on a live connector.
- **Primary metric:** first report shared within 14 days.
- **Guardrails:** real data-source connection rate, product-qualified account rate, and user confusion between demo and live data.
- **Planning target:** +3 points over six weeks.

## E4 — Checklist and templates

- **Hypothesis:** clearer next steps and useful templates help users build and share their first report.
- **Primary metric:** observed `report_shared` within 14 days.
- **Guardrails:** time-to-value, use of custom reports and no increase in misleading/low-quality shared reports.
- **Planning target:** +2 points over four weeks.

## E5 — Paid-social landing-page test

- **Hypothesis:** making the target use case clearer improves the share of paid-social trials that activate.
- **Primary metric:** activation per account owner, with activation measurement caveat applied.
- **Guardrails:** qualified-account volume and CAC per activated account.
- **Planning target:** +3 points over four weeks.
- **Important:** do not reallocate major spend based on the current channel table; there is no spend/CAC data in this dataset.

## Reading the generated experiment table

The repository also contains three **synthetic readouts** for checklist, OAuth and templates. Approximate 95% confidence intervals for all three activation differences include zero in the current run. They are examples for practising experiment analysis, not evidence that a real company shipped these variants.

## Before launch

For each real test, agree on the unit of randomization (account), primary metric, guardrails, minimum detectable effect, required sample size, runtime, exclusions, and stopping rule. Keep a record of the decision even when the result is inconclusive.

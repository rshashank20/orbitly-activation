# Root-cause notes — Orbitly activation and retention

I started with three explanations from the growth lead: acquisition quality, onboarding friction and weak product stickiness. The generated data lets me compare those explanations, but it cannot establish real-company causes. I have kept the distinction between a measured pattern and an interpretation explicit.

## 1. The connection step is the clearest funnel problem

The sequential user funnel loses **6,229 users between workspace creation and data-source connection**. That is the largest absolute drop, and equals **39.8% of users who reached workspace creation**.

Connection-failure events add context:

- **49.8%** of users who attempted a connection and never succeeded stopped after one attempt.
- `unknown_error` accounts for **29.2%** of deduplicated failure events.
- `oauth_denied` accounts for **27.2%**. Together they are **56.4%** of the failure-event mix.

That pattern makes error-specific guidance and recovery a reasonable first test. The data doesn't include session recordings or interviews, so I can't say users left *because* an error was confusing. It's the leading hypothesis to validate, not a proven causal root cause.

## 2. Connection is also associated with retention

Among accounts with an observable 90-day outcome, accounts whose primary user connected a data source in the first seven days had **54.6%** retention, compared with **30.6%** for accounts where that action wasn't observed. The gap is **+18.4 percentage points after standardizing within acquisition channel**, the largest adjusted gap among the actions I tested.

This is an association. More motivated or better-fit accounts may both connect and retain. It doesn't prove that pushing every user to connect will create an 18.4-point retention lift.

Orbitly's product-defined activation event is still `report_shared`. Its channel-adjusted retention gap is **+15.9 points**. However, the data generator deliberately hides some share events to simulate ad-blocker undercount, so observed activation isn't a perfect measurement of the underlying behavior.

## 3. Longer time-to-value is a warning sign, not a causal result

Accounts with an observed shared report within 24 hours had **59.6%** 90-day retention. The >96-hour group had **42.3%** retention. But the 24–48-hour group was at **61.6%**, so the relationship isn't a neat step-by-step decline.

I would treat very slow activation as a useful risk signal and test whether recovery nudges help. I wouldn't claim that reducing TTV by itself causes the entire retention gap.

## 4. Channel quality deserves a test, not a budget cut yet

Referral accounts had **34.5%** observed activation and **32.7%** paid conversion. Paid-social accounts had **5.2%** activation and **9.3%** paid conversion in this synthetic run. That is a large difference worth investigating.

But the dataset has no spend or CAC by channel, and some paid accounts have no observed activation event. That could be low product engagement, missing event capture, or both. I therefore would not recommend reallocating 25% of the marketing budget based on this evidence alone.

## 5. The experiment readouts don't settle the question

The generated checklist, OAuth and templates readouts all have approximate 95% confidence intervals that include zero. OAuth has a positive point estimate, but it isn't a validated win in this run. The data is synthetic and should be used to practise experiment interpretation, not presented as a real A/B test.

## Working diagnosis

The evidence supports a **connection-friction hypothesis** as the first thing to test. Two adjacent tasks should happen in parallel:

1. Improve connection recovery (clear errors, guided retry and a sample-data route).
2. Fix activation measurement so the `report_shared` event isn't lost to ad blockers.

I would also run a properly powered test of channel quality before making any major spend changes. Product stickiness isn't ruled out; the data simply gives a more specific early-funnel problem to investigate first.

## What would change my mind?

- If a guided connection flow does not improve successful connection or activation in a randomized test, the onboarding hypothesis weakens.
- If server-side event capture materially raises measured activation without changing behavior, some of the apparent activation gap was measurement-related.
- If the channel gap disappears after accounting for use case, account size or CAC, a budget shift may not be justified.
- If connected accounts still fail to retain after a cleaner connection experience, investigate fit and ongoing product value rather than assuming onboarding is the whole problem.

All counts and rates above are calculated from the seeded synthetic database. The intervention effects remain unproven until tested.

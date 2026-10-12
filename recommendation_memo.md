# Orbitly — activation analysis: recommendation memo

**To:** Growth lead and Product lead  
**From:** Business Analyst / Growth Analytics  
**Data:** Seeded synthetic dataset; findings are not real-company metrics

## Recommendation

I would start with the data-source connection step, and pair that work with an activation-instrumentation fix. I would not move marketing budget yet, and I would not treat any of the three generated experiment readouts as a validated win.

## Why this is the first place to work

The sequential user funnel loses **6,229 users between workspace creation and data-source connection**—the largest absolute step loss. Among users who tried but never connected, **49.8% stopped after one failed attempt**. `unknown_error` and `oauth_denied` account for **56.4%** of the deduplicated connection-failure events.

That makes the connection step the clearest place to test a fix. The data doesn't prove that unclear errors cause the abandonment, so I would use a pilot to validate the hypothesis rather than promise a specific lift.

The retention analysis gives this area another reason to investigate: early `data_source_connected` is associated with a **+18.4 percentage-point channel-adjusted gap** in 90-day account retention. That's useful evidence, but it is still observational. Better-fit or more motivated accounts may be more likely to connect in the first place.

## What I would do next

1. **Instrument activation properly.** The data generator deliberately drops about 8% of true `report_shared` events to simulate ad-blocker undercount. Before using activation as a company-wide target, reconcile it against server-side share events.
2. **Pilot error-specific connection recovery.** Show a helpful explanation for each known error and a guided retry. Keep a sample-data route available to users who can't connect a source immediately.
3. **Pre-register a follow-up experiment.** Measure connection completion first and report-share activation downstream. Define guardrails, required sample size and a stopping rule before launch.
4. **Investigate channel economics before changing spend.** Paid-social account activation is 5.2% in this dataset, versus 34.5% for referral, but no spend/CAC data is available. Ask Marketing for CAC per qualified and activated account before making a reallocation call.
5. **Don't over-read the existing synthetic tests.** All three approximate 95% intervals include zero. OAuth's positive point estimate is a reason to test again, not to declare a win.

## ARR scenario

The Excel model estimates that a **5 percentage-point increase in account-level observed activation** could imply about **$1.16M in retention-adjusted exit ARR**, using the current account volume, paid conversion among activated accounts, average MRR and an assumed 45% 12-month retention rate.

This is a modelled scenario, not money generated or a forecast. The retention curve is an assumption, and the model only makes sense if the activation lift represents genuine additional value-reaching accounts—not just better event capture. The model should be refreshed when those inputs are validated.

## Decision requested

- Approve a small connection-recovery pilot and the server-side activation instrumentation work.
- Ask Marketing for channel spend/CAC and qualified-account definitions before any budget change.
- Require a pre-registered experiment with account-level assignment, confidence intervals and guardrails before a wider rollout.

If the connection experiment does not improve successful connections, I would revisit the hypothesis rather than keep expanding the same solution. The aim is to learn where the drop actually comes from, not to make a preselected solution look right.

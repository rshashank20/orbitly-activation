# User stories — improve Orbitly's first-trial experience

These stories are based on the funnel and connection-error analysis. They are proposed requirements for a future build, not features that have already shipped.

## US-1 — Explain connection failures

**As a** new user trying to connect a marketing data source, **I want** an error message that tells me what failed and how to fix it, **so that** I can recover without guessing.

Acceptance criteria:
- Every `data_source_connect_failed` error maps to a reviewed user-facing help message.
- The message gives one clear next action (for example, review permissions or retry authentication).
- The raw error code remains available to Engineering for diagnosis.
- The event records which help message was displayed so outcomes can be compared.

## US-2 — Retry after a failed connection

**As a** user whose first connection attempt failed, **I want** a guided retry that preserves the selected data source, **so that** I don't have to restart the setup.

Acceptance criteria:
- Only users with at least one failed attempt and no later successful connection are eligible.
- A reminder is sent no sooner than the agreed cooldown and is suppressed if the user has since connected.
- The link returns the user to the failed step with prior non-sensitive inputs preserved.
- Unsubscribe and notification preferences are honored.

## US-3 — Explore with sample data

**As a** user who cannot connect a live source immediately, **I want** to explore a clearly labelled sample workspace, **so that** I can judge whether Orbitly is useful before resolving the integration.

Acceptance criteria:
- Sample workspace opens within the agreed performance target.
- Sample data is visibly labelled and never mixed silently with live customer data.
- A persistent action lets the user connect a real source.
- Analytics distinguish sample workspaces from live-data workspaces.

## US-4 — Measure activation reliably

**As a** Growth PM, **I want** the activation event to be recorded reliably, **so that** the team can distinguish a true product drop-off from a missing analytics event.

Acceptance criteria:
- `report_shared` is recorded server-side or reconciled against a server-confirmed share action.
- Event definitions and timestamps are documented and tested.
- A daily monitor flags unexplained event-volume drops and differences between client and server counts.
- Dashboards label the current observed activation rate as undercounted until the measurement fix is validated.

## US-5 — Experiment readout

**As a** Growth lead, **I want** experiment results to show sample sizes, effect size, confidence interval and guardrails, **so that** I don't call a noisy point estimate a win.

Acceptance criteria:
- Each account belongs to one variant for the duration of the test.
- Primary metric and decision rule are recorded before launch.
- Results include both activation and paid conversion, where the observation window permits it.
- A result is labelled inconclusive if its interval includes zero or a guardrail fails.

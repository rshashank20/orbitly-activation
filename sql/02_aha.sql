-- Account-level aha-moment analysis.
-- The retention outcome is account-level, so the unit here is an account, not a user.
-- The primary (earliest direct) signup determines acquisition channel and the 7-day window.
-- Product actions are taken from the primary user so the action and account outcome align.
-- The final gap is standardized within channel to reduce acquisition-mix confounding.
-- report_shared may be under-recorded by the seeded ad-blocker issue; absence is not proof the user never shared.
WITH ranked_users AS (
    SELECT account_id, user_id, acquisition_channel, signup_at, is_bot,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY signup_at, user_id) AS rn
    FROM users
), primary_user AS (
    SELECT account_id, user_id, acquisition_channel, signup_at, rn
    FROM ranked_users WHERE rn=1 AND is_bot=0
),
base AS (
    SELECT p.account_id, p.user_id, p.acquisition_channel, p.signup_at, s.retained_90d
    FROM primary_user p
    JOIN subscriptions s ON s.account_id = p.account_id
    WHERE p.rn = 1 AND s.retained_90d IS NOT NULL
),
actions AS (
    SELECT b.account_id, b.acquisition_channel, b.retained_90d,
           MAX(CASE WHEN e.event_name = 'workspace_created' THEN 1 ELSE 0 END) AS did_workspace,
           MAX(CASE WHEN e.event_name = 'data_source_connected' THEN 1 ELSE 0 END) AS did_connect,
           MAX(CASE WHEN e.event_name = 'report_created' THEN 1 ELSE 0 END) AS did_report,
           MAX(CASE WHEN e.event_name = 'report_shared' THEN 1 ELSE 0 END) AS did_share,
           MAX(CASE WHEN e.event_name = 'template_used' THEN 1 ELSE 0 END) AS did_template,
           MAX(CASE WHEN e.event_name = 'report_viewed' THEN 1 ELSE 0 END) AS did_view
    FROM base b
    LEFT JOIN v_events e ON e.user_id = b.user_id
         AND e.event_at_utc >= b.signup_at
         AND e.event_at_utc <= datetime(b.signup_at, '+7 days')
    GROUP BY b.account_id, b.acquisition_channel, b.retained_90d
),
long AS (
    SELECT account_id, acquisition_channel, retained_90d, 'workspace_created' AS action, did_workspace AS did FROM actions UNION ALL
    SELECT account_id, acquisition_channel, retained_90d, 'data_source_connected', did_connect FROM actions UNION ALL
    SELECT account_id, acquisition_channel, retained_90d, 'report_created', did_report FROM actions UNION ALL
    SELECT account_id, acquisition_channel, retained_90d, 'report_shared', did_share FROM actions UNION ALL
    SELECT account_id, acquisition_channel, retained_90d, 'template_used', did_template FROM actions UNION ALL
    SELECT account_id, acquisition_channel, retained_90d, 'report_viewed', did_view FROM actions
),
channel_rates AS (
    SELECT action, acquisition_channel,
           COUNT(*) AS accounts,
           SUM(did) AS doers,
           SUM(CASE WHEN did = 1 THEN retained_90d ELSE 0 END) * 1.0 / NULLIF(SUM(did), 0) AS ret_doers,
           SUM(CASE WHEN did = 0 THEN retained_90d ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN did = 0 THEN 1 ELSE 0 END), 0) AS ret_nondoers,
           (SUM(CASE WHEN did = 1 THEN retained_90d ELSE 0 END) * 1.0 / NULLIF(SUM(did), 0))
           - (SUM(CASE WHEN did = 0 THEN retained_90d ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN did = 0 THEN 1 ELSE 0 END), 0)) AS gap
    FROM long
    GROUP BY action, acquisition_channel
),
channel_weights AS (
    SELECT acquisition_channel,
           COUNT(*) * 1.0 / (SELECT COUNT(*) FROM base) AS weight
    FROM base
    GROUP BY acquisition_channel
),
pooled AS (
    SELECT action,
           SUM(doers) AS doers,
           SUM(accounts) AS accounts,
           SUM(doers * ret_doers) / NULLIF(SUM(doers), 0) AS ret_doers,
           SUM((accounts - doers) * ret_nondoers) / NULLIF(SUM(accounts - doers), 0) AS ret_nondoers,
           SUM(gap * weight) / NULLIF(SUM(CASE WHEN gap IS NOT NULL THEN weight ELSE 0 END), 0) AS adjusted_gap
    FROM channel_rates cr
    JOIN channel_weights cw USING (acquisition_channel)
    GROUP BY action
)
SELECT action, accounts, doers,
       ROUND(100.0 * ret_doers, 1) AS ret_doers_pct,
       ROUND(100.0 * ret_nondoers, 1) AS ret_nondoers_pct,
       ROUND(100.0 * (ret_doers - ret_nondoers), 1) AS raw_gap_pt,
       ROUND(100.0 * adjusted_gap, 1) AS channel_adjusted_gap_pt
FROM pooled
ORDER BY channel_adjusted_gap_pt DESC;

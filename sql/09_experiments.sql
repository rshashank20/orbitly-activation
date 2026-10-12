-- Experiment readouts at the randomization unit (account).
-- Activation uses the primary signup account member's report_shared event in the 14 days
-- after the recorded experiment start. Outcomes are directional, not statistical proof.
WITH ranked_users AS (
    SELECT account_id, user_id, signup_at, is_bot,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY signup_at,user_id) AS rn
    FROM users
), primary_user AS (
    SELECT account_id,user_id,signup_at,rn
    FROM ranked_users WHERE rn=1 AND is_bot=0
),
exp_base AS (
    SELECT x.experiment_id,x.variant,x.account_id,p.user_id,p.signup_at,x.started_at,
           CASE WHEN s.converted_at IS NOT NULL THEN 1 ELSE 0 END AS converted
    FROM experiments x
    JOIN primary_user p ON p.account_id=x.account_id AND p.rn=1
    LEFT JOIN subscriptions s ON s.account_id=x.account_id
),
flags AS (
    SELECT b.experiment_id,b.variant,b.account_id,b.converted,
           MAX(CASE WHEN e.event_name='report_shared'
                     AND e.event_at_utc >= b.started_at
                     AND e.event_at_utc <= datetime(b.started_at,'+14 days')
                    THEN 1 ELSE 0 END) AS activated
    FROM exp_base b
    LEFT JOIN v_events e ON e.user_id=b.user_id
    GROUP BY b.experiment_id,b.variant,b.account_id,b.converted
)
SELECT experiment_id,variant,COUNT(*) AS n_accounts,
       SUM(activated) AS activated_accounts,
       ROUND(100.0*AVG(activated),1) AS activation_pct,
       SUM(converted) AS paying_accounts,
       ROUND(100.0*AVG(converted),1) AS paid_account_pct
FROM flags
GROUP BY experiment_id,variant
ORDER BY experiment_id,variant;

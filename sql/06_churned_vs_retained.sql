-- Compare account engagement in days 8-30 for mature converted accounts.
-- LEFT JOIN is intentional: accounts with no observed events stay in the analysis as zeros.
WITH ranked_users AS (
    SELECT account_id, user_id, signup_at, is_bot,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY signup_at,user_id) AS rn
    FROM users
), primary_user AS (
    SELECT account_id,user_id,signup_at,rn
    FROM ranked_users WHERE rn=1 AND is_bot=0
),
base AS (
    SELECT p.account_id, p.user_id AS primary_user_id, p.signup_at, s.retained_90d
    FROM primary_user p
    JOIN subscriptions s ON s.account_id=p.account_id
    WHERE p.rn=1 AND s.converted_at IS NOT NULL AND s.retained_90d IS NOT NULL
),
account_events AS (
    SELECT b.account_id, b.retained_90d,
           COUNT(DISTINCT e.event_name) AS breadth,
           COUNT(e.event_id) AS n_events,
           COUNT(DISTINCT CASE WHEN e.event_name='report_viewed' THEN e.event_id END) AS reports_viewed,
           COUNT(DISTINCT date(e.event_at_utc)) AS active_days
    FROM base b
    LEFT JOIN v_events e ON e.user_id=b.primary_user_id
         AND e.event_at_utc BETWEEN datetime(b.signup_at,'+8 days') AND datetime(b.signup_at,'+30 days')
    GROUP BY b.account_id,b.primary_user_id,b.retained_90d
)
SELECT retained_90d AS retained, COUNT(*) AS accounts,
       ROUND(AVG(breadth),1) AS avg_event_breadth,
       ROUND(AVG(n_events),1) AS avg_events,
       ROUND(AVG(active_days),1) AS avg_active_days
FROM account_events
GROUP BY retained_90d
ORDER BY retained_90d;

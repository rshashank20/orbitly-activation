-- 08_retention_curves.sql — % of cohort active at day 7/14/30/60/90 (UTC-normalized)
WITH cohorts AS (
    SELECT user_id, strftime('%Y-%m', signup_at) AS cohort, signup_at
    FROM users
    WHERE is_bot = 0 AND invited_by IS NULL
),
active AS (
    SELECT c.cohort, c.user_id,
           MAX(CASE WHEN e.event_at_utc BETWEEN datetime(c.signup_at,'+4 days')
                                             AND datetime(c.signup_at,'+10 days') THEN 1 ELSE 0 END) AS d7,
           MAX(CASE WHEN e.event_at_utc BETWEEN datetime(c.signup_at,'+11 days')
                                             AND datetime(c.signup_at,'+17 days') THEN 1 ELSE 0 END) AS d14,
           MAX(CASE WHEN e.event_at_utc BETWEEN datetime(c.signup_at,'+27 days')
                                             AND datetime(c.signup_at,'+33 days') THEN 1 ELSE 0 END) AS d30,
           MAX(CASE WHEN e.event_at_utc BETWEEN datetime(c.signup_at,'+57 days')
                                             AND datetime(c.signup_at,'+63 days') THEN 1 ELSE 0 END) AS d60,
           MAX(CASE WHEN e.event_at_utc BETWEEN datetime(c.signup_at,'+87 days')
                                             AND datetime(c.signup_at,'+93 days') THEN 1 ELSE 0 END) AS d90
    FROM cohorts c
    LEFT JOIN v_events e ON e.user_id = c.user_id
         AND e.event_at_utc > c.signup_at
    GROUP BY c.cohort, c.user_id
)
SELECT cohort, COUNT(*) AS n,
       ROUND(100.0*AVG(d7),1) AS d7, ROUND(100.0*AVG(d14),1) AS d14,
       ROUND(100.0*AVG(d30),1) AS d30, ROUND(100.0*AVG(d60),1) AS d60,
       ROUND(100.0*AVG(d90),1) AS d90
FROM active
GROUP BY cohort
ORDER BY cohort;

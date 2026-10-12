-- 07_abandon.sql — onboarding friction: attempts vs failures per step + error breakdown
WITH attempts AS (
    SELECT u.user_id,
           COUNT(DISTINCT CASE WHEN e.event_name='data_source_connect_attempted' THEN json_extract(e.properties,'$.attempt') END) AS n_attempts,
           MAX(CASE WHEN e.event_name='data_source_connected' THEN 1 ELSE 0 END) AS connected
    FROM users u
    LEFT JOIN v_events e ON e.user_id = u.user_id
    WHERE u.is_bot = 0 AND u.invited_by IS NULL
      AND EXISTS (SELECT 1 FROM v_events e2
                  WHERE e2.user_id=u.user_id AND e2.event_name='workspace_created')
    GROUP BY u.user_id
)
SELECT 'attempted_but_never_connected' AS metric,
       COUNT(*) AS users
FROM attempts WHERE n_attempts > 0 AND connected = 0
UNION ALL
SELECT 'avg_attempts_per_user', ROUND(AVG(n_attempts),2) FROM attempts
UNION ALL
SELECT 'pct_abandon_after_1_failed_attempt',
       ROUND(100.0*SUM(CASE WHEN n_attempts=1 AND connected=0 THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN n_attempts>=1 AND connected=0 THEN 1 ELSE 0 END),0),1)
FROM attempts;
-- error breakdown (separate statement: CTEs don't cross statements)
WITH failures AS (
    SELECT DISTINCT e.user_id, json_extract(e.properties,'$.error') AS err,
           strftime('%Y-%m-%d %H:%M', e.event_at_utc) AS event_minute
    FROM v_events e
    JOIN users u ON u.user_id=e.user_id
    WHERE e.event_name='data_source_connect_failed'
      AND u.is_bot=0 AND u.invited_by IS NULL
),
errors AS (
    SELECT err, COUNT(*) AS n FROM failures GROUP BY err
)
SELECT err, n, ROUND(100.0*n/SUM(n) OVER (),1) AS pct
FROM errors ORDER BY n DESC;

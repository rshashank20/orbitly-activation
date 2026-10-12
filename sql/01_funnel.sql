-- User-level onboarding path within the 14-day trial. 'not_marked_invited' means invited_by is NULL; it is not a deduplicated account count.
-- Events are UTC-normalized in v_events. Each stage must happen after the prior stage.
-- Paid conversion and 90-day retention are account-level and are shown separately in the dashboard.
WITH genuine AS (
    SELECT user_id, strftime('%Y-%m', signup_at) AS cohort,
           CASE WHEN invited_by IS NULL THEN 'not_marked_invited' ELSE 'invited' END AS segment,
           signup_at
    FROM users
    WHERE is_bot=0
), raw_times AS (
    SELECT g.user_id, g.cohort, g.segment, g.signup_at,
           MIN(CASE WHEN e.event_name='workspace_created' THEN e.event_at_utc END) AS workspace_at,
           MIN(CASE WHEN e.event_name='data_source_connected' THEN e.event_at_utc END) AS connect_at,
           MIN(CASE WHEN e.event_name='report_created' THEN e.event_at_utc END) AS report_at,
           MIN(CASE WHEN e.event_name='report_shared' THEN e.event_at_utc END) AS share_at,
           MIN(CASE WHEN e.event_name='week2_active' THEN e.event_at_utc END) AS week2_at
    FROM genuine g
    LEFT JOIN v_events e ON e.user_id=g.user_id
       AND e.event_at_utc >= g.signup_at
       AND e.event_at_utc < datetime(g.signup_at,'+14 days')
    GROUP BY g.user_id,g.cohort,g.segment,g.signup_at
), flags AS (
    SELECT *,
      CASE WHEN workspace_at IS NOT NULL THEN 1 ELSE 0 END AS ws,
      CASE WHEN workspace_at IS NOT NULL AND connect_at > workspace_at THEN 1 ELSE 0 END AS connected,
      CASE WHEN workspace_at IS NOT NULL AND connect_at > workspace_at AND report_at > connect_at THEN 1 ELSE 0 END AS report_created,
      CASE WHEN workspace_at IS NOT NULL AND connect_at > workspace_at AND report_at > connect_at AND share_at > report_at THEN 1 ELSE 0 END AS activated,
      CASE WHEN workspace_at IS NOT NULL AND connect_at > workspace_at AND report_at > connect_at AND share_at > report_at AND week2_at > share_at THEN 1 ELSE 0 END AS week2_active
    FROM raw_times
), agg AS (
    SELECT cohort,segment,COUNT(*) AS signups,
           SUM(ws) AS workspace_users, SUM(connected) AS connected_users,
           SUM(report_created) AS report_users, SUM(activated) AS activated_users,
           SUM(week2_active) AS week2_users
    FROM flags
    GROUP BY cohort,segment
)
SELECT cohort,segment,signups,workspace_users,connected_users,report_users,activated_users,week2_users,
       ROUND(100.0*workspace_users/signups,1) AS pct_workspace,
       ROUND(100.0*connected_users/signups,1) AS pct_connected,
       ROUND(100.0*report_users/signups,1) AS pct_report_created,
       ROUND(100.0*activated_users/signups,1) AS pct_activated,
       ROUND(100.0*week2_users/signups,1) AS pct_week2_active
FROM agg
ORDER BY cohort,segment;

-- 04_drop.sql — step-by-step funnel loss within the 14-day onboarding window.
-- Stage counts are nested; a later event only counts when the preceding stage was completed first.
WITH funnel_base AS (
  SELECT user_id, signup_at FROM users WHERE is_bot=0 AND invited_by IS NULL
), times AS (
  SELECT g.user_id,g.signup_at,
    MIN(CASE WHEN e.event_name='workspace_created' THEN e.event_at_utc END) ws,
    MIN(CASE WHEN e.event_name='data_source_connected' THEN e.event_at_utc END) conn,
    MIN(CASE WHEN e.event_name='report_created' THEN e.event_at_utc END) report,
    MIN(CASE WHEN e.event_name='report_shared' THEN e.event_at_utc END) share,
    MIN(CASE WHEN e.event_name='week2_active' THEN e.event_at_utc END) week2
  FROM funnel_base g LEFT JOIN v_events e ON e.user_id=g.user_id
    AND e.event_at_utc>=g.signup_at AND e.event_at_utc<datetime(g.signup_at,'+14 days')
  GROUP BY g.user_id,g.signup_at
), f AS (
  SELECT *,
    CASE WHEN ws IS NOT NULL THEN 1 ELSE 0 END ws_ok,
    CASE WHEN ws IS NOT NULL AND conn>ws THEN 1 ELSE 0 END conn_ok,
    CASE WHEN ws IS NOT NULL AND conn>ws AND report>conn THEN 1 ELSE 0 END report_ok,
    CASE WHEN ws IS NOT NULL AND conn>ws AND report>conn AND share>report THEN 1 ELSE 0 END share_ok,
    CASE WHEN ws IS NOT NULL AND conn>ws AND report>conn AND share>report AND week2>share THEN 1 ELSE 0 END week2_ok
  FROM times
), totals AS (
  SELECT COUNT(*) signups,SUM(ws_ok) ws,SUM(conn_ok) conn,SUM(report_ok) report,
         SUM(share_ok) share,SUM(week2_ok) week2 FROM f
), stages AS (
  SELECT 1 ord,'signup -> workspace' step, signups entered, signups-ws lost FROM totals UNION ALL
  SELECT 2,'workspace -> connect',ws,ws-conn FROM totals UNION ALL
  SELECT 3,'connect -> report',conn,conn-report FROM totals UNION ALL
  SELECT 4,'report -> share (activation)',report,report-share FROM totals UNION ALL
  SELECT 5,'share -> week 2 active',share,share-week2 FROM totals
)
SELECT step,entered,lost,
       ROUND(100.0*lost/NULLIF(entered,0),1) AS pct_lost_of_entered,
       ROUND(100.0*lost/(SELECT signups FROM totals),1) AS pct_of_all_signups
FROM stages ORDER BY ord;

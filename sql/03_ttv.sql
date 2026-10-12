-- Account-level time-to-value among accounts with an observable 90-day outcome.
-- First observed shared report by the primary user is used as the activation timestamp.
-- Accounts with a true share event hidden by the seeded ad-blocker issue are not represented in this cut.
WITH ranked_users AS (
    SELECT account_id, user_id, signup_at, is_bot,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY signup_at, user_id) AS rn
    FROM users
), primary_user AS (
    SELECT account_id, user_id, signup_at, rn
    FROM ranked_users WHERE rn=1 AND is_bot=0
),
base AS (
    SELECT p.account_id, p.user_id AS account_id_owner_user_id, p.signup_at, s.retained_90d
    FROM primary_user p
    JOIN subscriptions s ON s.account_id = p.account_id
    WHERE p.rn = 1 AND s.retained_90d IS NOT NULL
),
ttv AS (
    SELECT b.account_id, b.retained_90d,
           (julianday(MIN(e.event_at_utc)) - julianday(b.signup_at)) * 24.0 AS ttv_h
    FROM base b
    JOIN v_events e ON e.user_id = b.account_id_owner_user_id
    WHERE e.event_name = 'report_shared'
      AND e.event_at_utc >= b.signup_at
      AND e.event_at_utc < datetime(b.signup_at, '+14 days')
    GROUP BY b.account_id, b.account_id_owner_user_id, b.signup_at, b.retained_90d
),
buckets AS (
    SELECT *, CASE WHEN ttv_h < 24 THEN '<24h'
                   WHEN ttv_h < 48 THEN '24-48h'
                   WHEN ttv_h < 96 THEN '48-96h'
                   ELSE '>96h' END AS bucket
    FROM ttv
    WHERE ttv_h IS NOT NULL AND ttv_h >= 0
)
SELECT bucket, COUNT(*) AS accounts,
       ROUND(AVG(ttv_h), 1) AS avg_hours,
       ROUND(100.0 * AVG(retained_90d), 1) AS retained_90d_pct
FROM buckets
GROUP BY bucket
ORDER BY avg_hours;

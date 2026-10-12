-- 10_dq.sql — data-quality audit appendix
-- bot rate over time
SELECT strftime('%Y-%m', signup_at) AS cohort,
       COUNT(*) AS signups,
       ROUND(100.0*AVG(is_bot),2) AS bot_pct,
       ROUND(100.0*AVG(CASE WHEN invited_by IS NOT NULL THEN 1 ELSE 0 END),1) AS invited_pct
FROM users
GROUP BY cohort
ORDER BY cohort;

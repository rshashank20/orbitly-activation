-- Acquisition-channel results at account level.
-- Each account is counted once, using its earliest direct signup as the owner/channel.
-- This avoids treating invited teammates as separate paying customers.
WITH ranked_users AS (
    SELECT account_id,user_id,acquisition_channel,signup_at,is_bot,
           ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY signup_at,user_id) AS rn
    FROM users
), primary_user AS (
    SELECT account_id,user_id,acquisition_channel,signup_at,rn
    FROM ranked_users WHERE rn=1 AND is_bot=0
),
base AS (
    SELECT p.account_id,p.user_id,p.acquisition_channel,p.signup_at,
           CASE WHEN s.converted_at IS NOT NULL THEN 1 ELSE 0 END AS paid
    FROM primary_user p
    LEFT JOIN subscriptions s ON s.account_id=p.account_id
    WHERE p.rn=1
),
account_flags AS (
    SELECT b.account_id,b.acquisition_channel,b.paid,
           MAX(CASE WHEN e.event_name='report_shared'
                     AND e.event_at_utc >= b.signup_at
                     AND e.event_at_utc <= datetime(b.signup_at,'+14 days')
                    THEN 1 ELSE 0 END) AS activated
    FROM base b
    LEFT JOIN v_events e ON e.user_id=b.user_id
    GROUP BY b.account_id,b.acquisition_channel,b.paid
)
SELECT acquisition_channel,
       COUNT(*) AS accounts,
       ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) AS pct_of_accounts,
       ROUND(100.0*AVG(activated),1) AS activation_pct,
       ROUND(100.0*AVG(paid),1) AS paid_conversion_pct,
       ROUND(100.0*SUM(CASE WHEN activated=1 AND paid=1 THEN 1 ELSE 0 END)
                    / NULLIF(SUM(activated),0),1) AS paid_rate_among_activated_pct,
       ROUND(100.0*SUM(CASE WHEN paid=1 AND activated=0 THEN 1 ELSE 0 END)
                    / NULLIF(SUM(paid),0),1) AS paid_accounts_without_activation_pct
FROM account_flags
GROUP BY acquisition_channel
ORDER BY activation_pct DESC;

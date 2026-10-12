-- Shared event view: normalize the known pre-June-2025 timezone issue.
-- The source has ~2% retry duplicates. For per-user yes/no flags, MAX() makes
-- duplicates irrelevant. Count-based analyses deduplicate within their own logic
-- (for example, connection attempts use the attempt property, not raw event rows).
DROP VIEW IF EXISTS v_events;
DROP TABLE IF EXISTS v_events_clean;
CREATE INDEX IF NOT EXISTS idx_events_user_name_time
    ON events(user_id, event_name, event_at);

CREATE VIEW v_events AS
SELECT event_id, user_id, event_name,
       CASE WHEN event_at < '2025-06-01'
            THEN datetime(event_at, '-5 hours', '-30 minutes')
            ELSE event_at
       END AS event_at_utc,
       properties
FROM events;

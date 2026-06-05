SELECT 
    session_id,
    user_id,
    -- Session duration calculation (in minutes)
    TIMESTAMPDIFF(MINUTE, MIN(event_timestamp), MAX(event_timestamp)) AS session_duration_minutes,
    -- Total scroll events
    COUNT(CASE WHEN event_type = 'scroll' THEN 1 END) AS scroll_count
FROM app_events
GROUP BY session_id, user_id
HAVING 
    -- 1. Duration more than 30 minutes
    TIMESTAMPDIFF(MINUTE, MIN(event_timestamp), MAX(event_timestamp)) > 30
    -- 2. At least 5 scroll events
    AND COUNT(CASE WHEN event_type = 'scroll' THEN 1 END) >= 5
    -- 3. Click-to-scroll ratio is less than 0.20
    AND (COUNT(CASE WHEN event_type = 'click' THEN 1 END) / COUNT(CASE WHEN event_type = 'scroll' THEN 1 END)) < 0.20
    -- 4. No purchases made during the session
    AND COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) = 0
ORDER BY 
    scroll_count DESC, 
    session_id ASC;
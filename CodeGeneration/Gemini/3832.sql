# Write your MySQL query statement below
WITH RankedStreaks AS (
    SELECT 
        user_id,
        action,
        -- The "Gaps and Islands" group identifier
        DATE_SUB(action_date, INTERVAL ROW_NUMBER() OVER(PARTITION BY user_id, action ORDER BY action_date) DAY) AS streak_group,
        COUNT(*) AS streak_length,
        MIN(action_date) AS start_date,
        MAX(action_date) AS end_date
    FROM activity
    GROUP BY 
        user_id, 
        action, 
        DATE_SUB(action_date, INTERVAL ROW_NUMBER() OVER(PARTITION BY user_id, action ORDER BY action_date) DAY)
),
FilteredAndRanked AS (
    SELECT 
        user_id,
        action,
        streak_length,
        start_date,
        end_date,
        -- Rank user streaks to find the maximum one
        ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY streak_length DESC) AS rn
    FROM RankedStreaks
    WHERE streak_length >= 5
)
SELECT 
    user_id,
    action,
    streak_length,
    start_date,
    end_date
FROM FilteredAndRanked
WHERE rn = 1
ORDER BY 
    streak_length DESC, 
    user_id ASC;
WITH ranked AS (
    SELECT
        user_id,
        action,
        action_date,
        DATE_SUB(action_date, INTERVAL ROW_NUMBER() OVER (
            PARTITION BY user_id, action
            ORDER BY action_date
        ) DAY) AS grp
    FROM activity
),
streaks AS (
    SELECT
        user_id,
        action,
        COUNT(*) AS streak_length,
        MIN(action_date) AS start_date,
        MAX(action_date) AS end_date
    FROM ranked
    GROUP BY user_id, action, grp
),
filtered AS (
    SELECT *
    FROM streaks
    WHERE streak_length >= 5
),
best AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY user_id
               ORDER BY streak_length DESC
           ) AS rn
    FROM filtered
)
SELECT
    user_id,
    action,
    streak_length,
    start_date,
    end_date
FROM best
WHERE rn = 1
ORDER BY streak_length DESC, user_id ASC;
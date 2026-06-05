WITH filtered AS (
    SELECT *
    FROM Stadium
    WHERE people >= 100
),
ranked AS (
    SELECT
        id,
        visit_date,
        people,
        id - ROW_NUMBER() OVER (ORDER BY id) AS grp
    FROM filtered
)
SELECT
    id,
    visit_date,
    people
FROM ranked
WHERE grp IN (
    SELECT grp
    FROM ranked
    GROUP BY grp
    HAVING COUNT(*) >= 3
)
ORDER BY visit_date;
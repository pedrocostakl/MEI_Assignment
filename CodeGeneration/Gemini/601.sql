WITH FilteredStadium AS (
SELECT id, visit_date, people,
id - ROW_NUMBER() OVER (ORDER BY id) AS grp
FROM Stadium
WHERE people >= 100
),
GroupCounts AS (
SELECT id, visit_date, people,
COUNT(*) OVER (PARTITION BY grp) AS cnt
FROM FilteredStadium
)
SELECT id, visit_date, people
FROM GroupCounts
WHERE cnt >= 3
ORDER BY visit_date ASC
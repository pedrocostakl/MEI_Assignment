WITH DayNumbers AS (
SELECT
submission_date,
DENSE_RANK() OVER (ORDER BY submission_date) AS day_num
FROM Submissions
),
HackerDailySubmissions AS (
SELECT
submission_date,
hacker_id,
COUNT(submission_id) AS sub_count
FROM Submissions
GROUP BY submission_date, hacker_id
),
HackerHistory AS (
SELECT
h.submission_date,
h.hacker_id,
h.sub_count,
d.day_num,
COUNT(DISTINCT prev.submission_date) AS consecutive_days
FROM HackerDailySubmissions h
JOIN DayNumbers d ON h.submission_date = d.submission_date
LEFT JOIN HackerDailySubmissions prev
ON prev.hacker_id = h.hacker_id
AND prev.submission_date <= h.submission_date
GROUP BY h.submission_date, h.hacker_id, h.sub_count, d.day_num
),
ConsistentHackersCount AS (
SELECT
submission_date,
COUNT(DISTINCT hacker_id) AS unique_consistent_hackers
FROM HackerHistory
WHERE consecutive_days = day_num
GROUP BY submission_date
),
RankedDailyMax AS (
SELECT
submission_date,
hacker_id,
ROW_NUMBER() OVER (
PARTITION BY submission_date
ORDER BY sub_count DESC, hacker_id ASC
) AS rn
FROM HackerDailySubmissions
)
SELECT
c.submission_date,
c.unique_consistent_hackers,
m.hacker_id,
h.name
FROM ConsistentHackersCount c
JOIN RankedDailyMax m ON c.submission_date = m.submission_date AND m.rn = 1
JOIN Hackers h ON m.hacker_id = h.hacker_id
ORDER BY c.submission_date;
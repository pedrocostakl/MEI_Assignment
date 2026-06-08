WITH daily_submissions AS (
    SELECT
        submission_date,
        hacker_id,
        COUNT(*) AS submissions
    FROM Submissions
    GROUP BY submission_date, hacker_id
),

top_hacker AS (
    SELECT
        submission_date,
        hacker_id,
        ROW_NUMBER() OVER (
            PARTITION BY submission_date
            ORDER BY submissions DESC, hacker_id
        ) AS rn
    FROM daily_submissions
),

consistent_hackers AS (
    SELECT
        s1.submission_date,
        COUNT(DISTINCT s1.hacker_id) AS hacker_count
    FROM Submissions s1
    WHERE (
        SELECT COUNT(DISTINCT s2.submission_date)
        FROM Submissions s2
        WHERE s2.hacker_id = s1.hacker_id
          AND s2.submission_date <= s1.submission_date
    ) = DATEDIFF(s1.submission_date, '2016-03-01') + 1
    GROUP BY s1.submission_date
)

SELECT
    ch.submission_date,
    ch.hacker_count,
    th.hacker_id,
    h.name
FROM consistent_hackers ch
JOIN top_hacker th
    ON ch.submission_date = th.submission_date
   AND th.rn = 1
JOIN Hackers h
    ON th.hacker_id = h.hacker_id
ORDER BY ch.submission_date;
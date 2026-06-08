WITH submission_totals AS (
    SELECT
        challenge_id,
        SUM(total_submissions) AS total_submissions,
        SUM(total_accepted_submissions) AS total_accepted_submissions
    FROM Submission_Stats
    GROUP BY challenge_id
),
view_totals AS (
    SELECT
        challenge_id,
        SUM(total_views) AS total_views,
        SUM(total_unique_views) AS total_unique_views
    FROM View_Stats
    GROUP BY challenge_id
)

SELECT
    c.contest_id,
    c.hacker_id,
    c.name,
    SUM(COALESCE(s.total_submissions, 0)) AS total_submissions,
    SUM(COALESCE(s.total_accepted_submissions, 0)) AS total_accepted_submissions,
    SUM(COALESCE(v.total_views, 0)) AS total_views,
    SUM(COALESCE(v.total_unique_views, 0)) AS total_unique_views
FROM Contests c
JOIN Colleges col
    ON c.contest_id = col.contest_id
JOIN Challenges ch
    ON col.college_id = ch.college_id
LEFT JOIN submission_totals s
    ON ch.challenge_id = s.challenge_id
LEFT JOIN view_totals v
    ON ch.challenge_id = v.challenge_id
GROUP BY
    c.contest_id,
    c.hacker_id,
    c.name
HAVING
      SUM(COALESCE(s.total_submissions, 0))
    + SUM(COALESCE(s.total_accepted_submissions, 0))
    + SUM(COALESCE(v.total_views, 0))
    + SUM(COALESCE(v.total_unique_views, 0)) > 0
ORDER BY c.contest_id;
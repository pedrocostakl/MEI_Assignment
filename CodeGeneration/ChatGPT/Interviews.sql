SELECT con.contest_id, con.hacker_id, con.name,
COALESCE(sub.sum_ts, 0) AS total_submissions,
COALESCE(sub.sum_tas, 0) AS total_accepted_submissions,
COALESCE(vw.sum_tv, 0) AS total_views,
COALESCE(vw.sum_tuv, 0) AS total_unique_views
FROM Contests con
JOIN Colleges col ON con.contest_id = col.contest_id
JOIN Challenges ch ON col.college_id = ch.college_id
LEFT JOIN (
SELECT challenge_id,
SUM(total_submissions) AS sum_ts,
SUM(total_accepted_submissions) AS sum_tas
FROM Submission_Stats
GROUP BY challenge_id
) sub ON ch.challenge_id = sub.challenge_id
LEFT JOIN (
SELECT challenge_id,
SUM(total_views) AS sum_tv,
SUM(total_unique_views) AS sum_tuv
FROM View_Stats
GROUP BY challenge_id
) vw ON ch.challenge_id = vw.challenge_id
GROUP BY con.contest_id, con.hacker_id, con.name
HAVING (COALESCE(SUM(sub.sum_ts), 0) +
COALESCE(SUM(sub.sum_tas), 0) +
COALESCE(SUM(vw.sum_tv), 0) +
COALESCE(SUM(vw.sum_tuv), 0)) > 0
ORDER BY con.contest_id
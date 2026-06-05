WITH ordered AS (
    SELECT
        s.*,
        ROW_NUMBER() OVER (
            PARTITION BY student_id
            ORDER BY session_date, session_id
        ) AS rn
    FROM study_sessions s
),
counts AS (
    SELECT
        student_id,
        COUNT(*) AS n
    FROM ordered
    GROUP BY student_id
),
valid_k AS (
    SELECT
        o.student_id,
        c.n,
        k.k AS cycle_length
    FROM counts c
    JOIN LATERAL generate_series(3, c.n / 2) AS k(k)
        ON (c.n % k.k = 0)
    JOIN ordered o ON o.student_id = c.student_id
    GROUP BY o.student_id, c.n, k.k
    HAVING
        -- pattern repetition check
        BOOL_AND(
            o.subject = (
                SELECT subject
                FROM ordered o2
                WHERE o2.student_id = o.student_id
                  AND o2.rn = ((o.rn - 1) % k.k) + 1
            )
        )
        -- date gap constraint (no gap > 2 days)
        AND NOT EXISTS (
            SELECT 1
            FROM ordered o3
            WHERE o3.student_id = o.student_id
              AND o3.rn > 1
              AND o3.session_date
                  - LAG(o3.session_date)
                    OVER (PARTITION BY o3.student_id ORDER BY o3.rn) > 2
        )
        -- at least 3 distinct subjects in cycle
        AND (
            SELECT COUNT(DISTINCT subject)
            FROM ordered o4
            WHERE o4.student_id = o.student_id
              AND o4.rn <= k.k
        ) >= 3
),
chosen AS (
    SELECT DISTINCT ON (student_id)
        student_id,
        cycle_length
    FROM valid_k
    ORDER BY student_id, cycle_length DESC
),
totals AS (
    SELECT
        student_id,
        SUM(hours_studied) AS total_study_hours
    FROM study_sessions
    GROUP BY student_id
)
SELECT
    st.student_id,
    st.student_name,
    st.major,
    ch.cycle_length,
    t.total_study_hours
FROM chosen ch
JOIN totals t ON t.student_id = ch.student_id
JOIN students st ON st.student_id = ch.student_id
ORDER BY
    ch.cycle_length DESC,
    t.total_study_hours DESC;
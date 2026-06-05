WITH OrderedSessions AS (
    -- Step 1: Sequence the sessions and check the date differences
    SELECT 
        student_id,
        subject,
        session_date,
        hours_studied,
        ROW_NUMBER() OVER(PARTITION BY student_id ORDER BY session_date) as rn,
        LAG(session_date) OVER(PARTITION BY student_id ORDER BY session_date) as prev_date
    FROM study_sessions
),
IslandGroups AS (
    -- Step 2: Create a group ID for streaks where consecutive dates have <= 2 days gap
    SELECT 
        student_id,
        subject,
        session_date,
        hours_studied,
        rn,
        SUM(CASE WHEN DATEDIFF(session_date, prev_date) > 2 THEN 1 ELSE 0 END) 
            OVER(PARTITION BY student_id ORDER BY session_date) as island_id
    FROM OrderedSessions
),
SequenceWithrn AS (
    -- Step 3: Re-index within each island to easily check lookahead/lookbehind patterns
    SELECT 
        student_id,
        subject,
        hours_studied,
        ROW_NUMBER() OVER(PARTITION BY student_id, island_id ORDER BY session_date) as seq_rn,
        COUNT(*) OVER(PARTITION BY student_id, island_id) as total_island_sessions,
        island_id
    FROM IslandGroups
),
ValidCycles AS (
    -- Step 4: Identify potential cycle lengths (N) where the pattern repeats for >= 2 full cycles
    SELECT DISTINCT
        s1.student_id,
        s1.island_id,
        -- The cycle length is determined by matching the first complete loop
        (
            SELECT COUNT(DISTINCT s2.subject)
            FROM SequenceWithrn s2
            WHERE s2.student_id = s1.student_id 
              AND s2.island_id = s1.island_id
              AND s2.seq_rn <= (
                  SELECT MIN(s3.seq_rn) 
                  FROM SequenceWithrn s3 
                  WHERE s3.student_id = s1.student_id 
                    AND s3.island_id = s1.island_id 
                    AND s3.seq_rn > 1 
                    AND s3.subject = (SELECT subject FROM SequenceWithrn WHERE student_id = s1.student_id AND island_id = s1.island_id AND seq_rn = 1)
              ) - 1
        ) AS cycle_length
    FROM SequenceWithrn s1
    -- Check if every session matches the session N steps ahead for a full 2 cycles
    -- Because the problem requires full 2 cycles, we look for matches and validate totals
),
FinalCalculation AS (
    -- Extract the exact valid pattern length and aggregate metrics
    SELECT 
        s.student_id,
        -- Find the number of distinct subjects in the first perfect cycle block
        COUNT(DISTINCT CASE WHEN s.seq_rn <= c.cycle_len THEN s.subject END) as cycle_length,
        SUM(s.hours_studied) as total_study_hours
    FROM SequenceWithrn s
    JOIN (
        -- Helper to cleanly map out the cycle lengths that pass all constraints per student
        SELECT 
            s1.student_id,
            s1.island_id,
            MAX(sub_match.cycle_candidate) as cycle_len
        FROM SequenceWithrn s1
        CROSS JOIN (SELECT 3 AS cycle_candidate UNION ALL SELECT 4 UNION ALL SELECT 5) sub_match -- Dynamic N check
        WHERE s1.total_island_sessions >= sub_match.cycle_candidate * 2
          -- Validate that the cycle shifts align perfectly
          AND NOT EXISTS (
              SELECT 1 
              FROM SequenceWithrn s2
              WHERE s2.student_id = s1.student_id AND s2.island_id = s1.island_id
                AND s2.seq_rn + sub_match.cycle_candidate <= s2.total_island_sessions
                AND s2.subject != (
                    SELECT s3.subject 
                    FROM SequenceWithrn s3 
                    WHERE s3.student_id = s2.student_id 
                      AND s3.island_id = s2.island_id 
                      AND s3.seq_rn = s2.seq_rn + sub_match.cycle_candidate
                )
          )
        GROUP BY s1.student_id, s1.island_id
    ) c ON s.student_id = c.student_id AND s.island_id = c.island_id
    -- Ensure we restrict the summation strictly to the 2 complete cycles matching the length criteria
    WHERE s.seq_rn <= c.cycle_len * 2
    GROUP BY s.student_id, c.island_id, c.cycle_len
    HAVING COUNT(DISTINCT s.subject) >= 3
)
-- Step 5: Join with the students table to pull profile names and sort output
SELECT 
    st.student_id,
    st.student_name,
    st.major,
    fc.cycle_length,
    fc.total_study_hours
FROM FinalCalculation fc
JOIN students st ON fc.student_id = st.student_id
ORDER BY fc.cycle_length DESC, fc.total_study_hours DESC;
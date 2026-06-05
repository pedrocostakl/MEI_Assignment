WITH top_users AS (
    SELECT 
        user_id
    FROM course_completions
    GROUP BY user_id
    HAVING COUNT(*) >= 5
       AND AVG(course_rating) >= 4
),
ordered_courses AS (
    SELECT
        user_id,
        course_name AS first_course,
        LEAD(course_name) OVER (
            PARTITION BY user_id
            ORDER BY completion_date
        ) AS second_course
    FROM course_completions
    WHERE user_id IN (SELECT user_id FROM top_users)
)
SELECT
    first_course,
    second_course,
    COUNT(*) AS transition_count
FROM ordered_courses
WHERE second_course IS NOT NULL
GROUP BY first_course, second_course
ORDER BY 
    transition_count DESC,
    first_course ASC,
    second_course ASC;
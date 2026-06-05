WITH RECURSIVE
-- 1) Compute hierarchy level (CEO = 1)
levels AS (
    SELECT
        employee_id,
        employee_name,
        manager_id,
        salary,
        department,
        1 AS level
    FROM Employees
    WHERE manager_id IS NULL

    UNION ALL

    SELECT
        e.employee_id,
        e.employee_name,
        e.manager_id,
        e.salary,
        e.department,
        l.level + 1
    FROM Employees e
    JOIN levels l
        ON e.manager_id = l.employee_id
),

-- 2) Build ancestor → descendant relationships
tree AS (
    -- each employee is an ancestor of themselves
    SELECT
        employee_id AS manager_id,
        employee_id AS employee_id
    FROM Employees

    UNION ALL

    -- propagate down the hierarchy
    SELECT
        t.manager_id,
        e.employee_id
    FROM tree t
    JOIN Employees e
        ON e.manager_id = t.employee_id
)

SELECT
    l.employee_id,
    l.employee_name,
    l.level,

    -- team size = all descendants except self
    COUNT(DISTINCT t.employee_id) - 1 AS team_size,

    -- budget = sum of all descendants including self
    SUM(e.salary) AS budget

FROM levels l
JOIN tree t
    ON l.employee_id = t.manager_id
JOIN Employees e
    ON e.employee_id = t.employee_id

GROUP BY
    l.employee_id,
    l.employee_name,
    l.level

ORDER BY
    l.level ASC,
    budget DESC,
    l.employee_name ASC;
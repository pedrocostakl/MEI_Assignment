# Write your MySQL query statement below
WITH RECURSIVE
  -- Step 1: Calculate the hierarchy level for each employee starting from the CEO (level 1)
  HierarchyLevels AS (
    SELECT 
      employee_id, 
      employee_name, 
      manager_id, 
      salary, 
      1 AS level
    FROM Employees
    WHERE manager_id IS NULL
    
    UNION ALL
    
    SELECT 
      e.employee_id, 
      e.employee_name, 
      e.manager_id, 
      e.salary, 
      hl.level + 1 AS level
    FROM Employees e
    JOIN HierarchyLevels hl ON e.manager_id = hl.employee_id
  ),

  -- Step 2: Build a mapping of all manager-subordinate pairs (both direct and indirect)
  -- We start with every employee as a subordinate to themselves (for the budget calculation)
  SubordinateMapping AS (
    SELECT 
      employee_id AS manager_id, 
      employee_id AS sub_id, 
      salary AS sub_salary,
      0 AS is_indirect  -- Flag to distinguish self vs actual reports for team size
    FROM Employees
    
    UNION ALL
    
    SELECT 
      e.manager_id, 
      sm.sub_id, 
      sm.sub_salary,
      1 AS is_indirect
    FROM Employees e
    JOIN SubordinateMapping sm ON e.employee_id = sm.manager_id
    WHERE e.manager_id IS NOT NULL
  ),

  -- Step 3: Aggregate the team size and total budget for each manager
  AggregatedMetrics AS (
    SELECT 
      manager_id,
      SUM(CASE WHEN is_indirect = 1 THEN 1 ELSE 0 END) AS team_size,
      SUM(sub_salary) AS budget
    FROM SubordinateMapping
    GROUP BY manager_id
  )

-- Step 4: Combine the hierarchy levels with the metrics and order the result
SELECT 
  hl.employee_id,
  hl.employee_name,
  hl.level,
  COALESCE(am.team_size, 0) AS team_size,
  COALESCE(am.budget, hl.salary) AS budget
FROM HierarchyLevels hl
LEFT JOIN AggregatedMetrics am ON hl.employee_id = am.manager_id
ORDER BY 
  hl.level ASC, 
  budget DESC, 
  hl.employee_name ASC;
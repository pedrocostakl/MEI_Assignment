CREATE FUNCTION getNthHighestSalary(N INT) RETURNS INT
BEGIN
  RETURN (
      WITH RankedSalaries AS (
          SELECT salary, 
                 DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
          FROM Employee
      )
      SELECT DISTINCT salary 
      FROM RankedSalaries 
      WHERE rnk = N
  );
END
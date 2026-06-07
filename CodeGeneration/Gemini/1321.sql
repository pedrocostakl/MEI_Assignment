WITH DailyAmount AS (
    SELECT 
        visited_on,
        SUM(amount) AS daily_sum
    FROM 
        Customer
    GROUP BY 
        visited_on
),
RollingMetrics AS (
    SELECT 
        visited_on,
        SUM(daily_sum) OVER(
            ORDER BY visited_on 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS amount,
        ROUND(
            AVG(daily_sum) OVER(
                ORDER BY visited_on 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ), 2
        ) AS average_amount,
        -- Generate a row number to filter out the first 6 days easily
        ROW_NUMBER() OVER(ORDER BY visited_on) AS row_num
    FROM 
        DailyAmount
)
SELECT 
    visited_on,
    amount,
    average_amount
FROM 
    RollingMetrics
WHERE 
    row_num >= 7
ORDER BY 
    visited_on ASC;
-- Step 1: Get the latest price for products that changed before or on 2019-08-16
SELECT product_id, new_price AS price
FROM Products
WHERE (product_id, change_date) IN (
    SELECT product_id, MAX(change_date)
    FROM Products
    WHERE change_date <= '2019-08-16'
    GROUP BY product_id
)

UNION

-- Step 2: Get products whose first price change happened AFTER 2019-08-16 and set them to 10
SELECT DISTINCT product_id, 10 AS price
FROM Products
GROUP BY product_id
HAVING MIN(change_date) > '2019-08-16';
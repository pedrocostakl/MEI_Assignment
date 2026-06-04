SELECT 
    CASE 
        -- If id is odd and it's the last row, keep it the same
        WHEN id % 2 = 1 AND id = (SELECT MAX(id) FROM Seat) THEN id
        -- If id is odd, swap with the next even id
        WHEN id % 2 = 1 THEN id + 1
        -- If id is even, swap with the previous odd id
        ELSE id - 1
    END AS id,
    student
FROM Seat
ORDER BY id ASC;
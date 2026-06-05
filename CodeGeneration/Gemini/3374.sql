WITH RECURSIVE SplitWords AS (
    -- Anchor member: Get the first word and the remainder of the string
    SELECT 
        content_id,
        content_text AS original_text,
        1 AS word_pos,
        -- Extract the first word up to the first space
        CASE 
            WHEN POSITION(' ' IN content_text) > 0 
            THEN SUBSTRING(content_text FROM 1 FOR POSITION(' ' IN content_text) - 1)
            ELSE content_text
        END AS current_word,
        -- Keep the remainder of the string
        CASE 
            WHEN POSITION(' ' IN content_text) > 0 
            THEN SUBSTRING(content_text FROM POSITION(' ' IN content_text) + 1)
            ELSE ''
        END AS remainder
    FROM user_content

    UNION ALL

    -- Recursive member: Process the remaining string word by word
    SELECT 
        content_id,
        original_text,
        word_pos + 1,
        CASE 
            WHEN POSITION(' ' IN remainder) > 0 
            THEN SUBSTRING(remainder FROM 1 FOR POSITION(' ' IN remainder) - 1)
            ELSE remainder
        END,
        CASE 
            WHEN POSITION(' ' IN remainder) > 0 
            THEN SUBSTRING(remainder FROM POSITION(' ' IN remainder) + 1)
            ELSE ''
        END
    FROM SplitWords
    WHERE remainder <> ''
),
CapitalizedWords AS (
    -- Apply capitalization rules to each split word (including hyphen handling)
    SELECT 
        content_id,
        original_text,
        word_pos,
        CASE 
            -- If the word contains a hyphen, split and capitalize both halves
            WHEN POSITION('-' IN current_word) > 0 THEN
                CONCAT(
                    UPPER(SUBSTRING(current_word FROM 1 FOR 1)),
                    LOWER(SUBSTRING(current_word FROM 2 FOR POSITION('-' IN current_word) - 2)),
                    '-',
                    UPPER(SUBSTRING(current_word FROM POSITION('-' IN current_word) + 1 FOR 1)),
                    LOWER(SUBSTRING(current_word FROM POSITION('-' IN current_word) + 2))
                )
            -- Normal word capitalization
            ELSE 
                CONCAT(
                    UPPER(SUBSTRING(current_word FROM 1 FOR 1)),
                    LOWER(SUBSTRING(current_word FROM 2))
                )
        END AS processed_word
    FROM SplitWords
)
-- Final step: Group by content_id and string-aggregate the words back together
SELECT 
    content_id,
    original_text,
    STRING_AGG(processed_word, ' ' ORDER BY word_pos) AS converted_text
FROM 
    CapitalizedWords
GROUP BY 
    content_id, original_text;
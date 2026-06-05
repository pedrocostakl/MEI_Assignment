WITH RECURSIVE word_split AS (
    -- Step 1: split by spaces
    SELECT
        content_id,
        content_text,
        SUBSTRING_INDEX(content_text, ' ', 1) AS word,
        SUBSTRING(content_text, LENGTH(SUBSTRING_INDEX(content_text, ' ', 1)) + 2) AS rest,
        1 AS word_pos
    FROM user_content

    UNION ALL

    SELECT
        content_id,
        content_text,
        SUBSTRING_INDEX(rest, ' ', 1),
        SUBSTRING(rest, LENGTH(SUBSTRING_INDEX(rest, ' ', 1)) + 2),
        word_pos + 1
    FROM word_split
    WHERE rest <> ''
),

hyphen_split AS (
    -- Step 2: split words by hyphen
    SELECT
        content_id,
        word_pos,
        SUBSTRING_INDEX(word, '-', 1) AS part,
        SUBSTRING(word, LENGTH(SUBSTRING_INDEX(word, '-', 1)) + 2) AS rest,
        1 AS part_pos
    FROM word_split

    UNION ALL

    SELECT
        content_id,
        word_pos,
        SUBSTRING_INDEX(rest, '-', 1),
        SUBSTRING(rest, LENGTH(SUBSTRING_INDEX(rest, '-', 1)) + 2),
        part_pos + 1
    FROM hyphen_split
    WHERE rest <> ''
),

capitalized AS (
    -- Step 3: capitalize each hyphen part
    SELECT
        content_id,
        word_pos,
        part_pos,
        CONCAT(UPPER(LEFT(part, 1)), LOWER(SUBSTRING(part, 2))) AS fixed_part
    FROM hyphen_split
),

rebuild_words AS (
    -- Step 4: rebuild hyphenated words
    SELECT
        content_id,
        word_pos,
        GROUP_CONCAT(fixed_part ORDER BY part_pos SEPARATOR '-') AS fixed_word
    FROM capitalized
    GROUP BY content_id, word_pos
)

-- Step 5: rebuild full sentence
SELECT
    u.content_id,
    u.content_text AS original_text,
    GROUP_CONCAT(r.fixed_word ORDER BY r.word_pos SEPARATOR ' ') AS converted_text
FROM user_content u
JOIN rebuild_words r
    ON u.content_id = r.content_id
GROUP BY u.content_id, u.content_text;
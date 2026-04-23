-- ==========================================
-- 1. POPULATE PROFESSORS
-- ==========================================
INSERT INTO professors (name, department) VALUES
('Dr. Alan Turing', 'Computer Science'),
('Dr. Ada Lovelace', 'Mathematics'),
('Dr. Richard Feynman', 'Physics'),
('Dr. Marie Curie', 'Chemistry');

-- ==========================================
-- 2. POPULATE STUDENTS
-- ==========================================
INSERT INTO students (name, email, enrollment_year) VALUES
('Alice Johnson', 'alice.j@university.edu', 2023),
('Bob Smith', 'bob.s@university.edu', 2023),
('Charlie Davis', 'charlie.d@university.edu', 2024),
('Diana Prince', 'diana.p@university.edu', 2022),
('Edward Nigma', 'e.nigma@university.edu', 2024);

-- ==========================================
-- 3. POPULATE COURSES
-- ==========================================
-- Referencing Professor IDs (1: Turing, 2: Lovelace, 3: Feynman)
INSERT INTO courses (title, credits, professor_id) VALUES
('Introduction to Algorithms', 4, 1),
('Linear Algebra', 3, 2),
('Quantum Mechanics', 4, 3),
('Data Structures', 4, 1);

-- ==========================================
-- 4. POPULATE ENROLLMENTS
-- ==========================================
-- Linking Students to Courses with some initial grades
INSERT INTO enrollments (student_id, course_id, grade) VALUES
(1, 1, 92.5), -- Alice in Algorithms
(1, 2, 88.0), -- Alice in Linear Algebra
(2, 1, 75.0), -- Bob in Algorithms
(3, 4, 95.0), -- Charlie in Data Structures
(4, 3, 91.0), -- Diana in Quantum Mechanics
(5, 1, 82.0); -- Edward in Algorithms

-- ==========================================
-- 5. POPULATE ASSIGNMENTS
-- ==========================================
INSERT INTO assignments (course_id, title, max_score) VALUES
(1, 'Sorting Algorithms Lab', 100),
(1, 'Graph Theory Quiz', 50),
(2, 'Matrix Transformation Set', 100),
(3, 'Schrödinger Equation Paper', 100),
(4, 'Binary Search Tree Implementation', 100);

-- ==========================================
-- 6. POPULATE SUBMISSIONS
-- ==========================================
INSERT INTO submissions (assignment_id, student_id, score, submitted_at) VALUES
(1, 1, 98.0, '2024-02-15 10:30:00'),
(1, 2, 70.0, '2024-02-15 14:20:00'),
(2, 1, 48.0, '2024-03-01 09:00:00'),
(3, 1, 85.0, '2024-02-20 11:00:00'),
(4, 4, 92.0, '2024-03-10 16:45:00'),
(5, 3, 95.0, '2024-03-12 08:15:00');
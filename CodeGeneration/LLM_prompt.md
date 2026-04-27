You are to generate a RESTful API in Python using FastAPI.

The API must implement endpoints based on the database schema below.

------------------------
DATABASE SCHEMA:
{-- Students
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    enrollment_year INT NOT NULL
);

-- Professors
CREATE TABLE professors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL
);

-- Courses
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    professor_id INT,
    FOREIGN KEY (professor_id) REFERENCES professors(id)
);

-- Enrollments (many-to-many Students <-> Courses)
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    grade FLOAT,
    UNIQUE(student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Assignments
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    course_id INT NOT NULL,
    title VARCHAR(100),
    max_score INT,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Submissions
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    assignment_id INT NOT NULL,
    student_id INT NOT NULL,
    score FLOAT,
    submitted_at TIMESTAMP,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);}
------------------------

GENERAL REQUIREMENTS:
- Use FastAPI
- Use SQLAlchemy ORM
- Use SQLite
- Code must be runnable as-is
- Include all imports
- Include database setup
- Include models and Pydantic schemas
- Include basic error handling
- Return proper HTTP status codes

------------------------
ENDPOINTS TO IMPLEMENT:
------------------------

EASY (basic CRUD):
1. POST /students → create a student
2. GET /students/{id} → retrieve a student

MEDIUM (relationships):
1. POST /courses → create a course with professor_id
2. POST /enrollments → enroll a student in a course

HARD (query + aggregation):
1. GET /courses/{id}/students → list students enrolled in a course
2. GET /courses/{id}/average-grade → compute average grade for the course

------------------------

OUTPUT FORMAT:
- Single file: main.py
- Must run with: uvicorn main:app --reload
- No explanations, only code
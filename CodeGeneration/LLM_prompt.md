You are to generate a RESTful API in Python using FastAPI.

The API must implement endpoints based on the database schema below.

------------------------
DATABASE SCHEMA:
{PASTE SCHEMA HERE}
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
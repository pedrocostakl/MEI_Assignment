from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import datetime
from typing import List, Optional

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./school.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    enrollment_year = Column(Integer, nullable=False)

class Professor(Base):
    __tablename__ = "professors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    credits = Column(Integer, nullable=False)
    professor_id = Column(Integer, ForeignKey("professors.id"))

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(100))
    max_score = Column(Integer)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class StudentBase(BaseModel):
    name: str
    email: str
    enrollment_year: int

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CourseCreate(BaseModel):
    title: str
    credits: int
    professor_id: int

class CourseResponse(CourseCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    grade: Optional[float] = None

class EnrollmentResponse(EnrollmentCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- FastAPI App ---
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

# EASY: 1. POST /students -> create a student
@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.model_dump())
    db.add(db_student)
    try:
        db.commit()
        db.refresh(db_student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_student

# EASY: 2. GET /students/{id} -> retrieve a student
@app.get("/students/{id}", response_model=StudentResponse)
def read_student(id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == id).first()
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

# MEDIUM: 1. POST /courses -> create a course with professor_id
@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    if course.professor_id is not None:
        prof = db.query(Professor).filter(Professor.id == course.professor_id).first()
        if not prof:
             raise HTTPException(status_code=404, detail="Professor not found")
    
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

# MEDIUM: 2. POST /enrollments -> enroll a student in a course
@app.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    db_course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    db_enrollment = Enrollment(**enrollment.model_dump())
    db.add(db_enrollment)
    try:
        db.commit()
        db.refresh(db_enrollment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")
    return db_enrollment

# HARD: 1. GET /courses/{id}/students -> list students enrolled in a course
@app.get("/courses/{id}/students", response_model=List[StudentResponse])
def get_students_in_course(id: int, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == id).all()
    return students

# HARD: 2. GET /courses/{id}/average-grade -> compute average grade for the course
@app.get("/courses/{id}/average-grade")
def get_course_average_grade(id: int, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    result = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == id, Enrollment.grade.isnot(None)).scalar()
    
    return {
        "course_id": id, 
        "average_grade": float(result) if result is not None else 0.0
    }
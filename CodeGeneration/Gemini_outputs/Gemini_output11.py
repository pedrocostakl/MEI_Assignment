from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError

# ==========================================
# Database Setup
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./school.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# SQLAlchemy Models
# ==========================================
class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    enrollment_year = Column(Integer, nullable=False)

    enrollments = relationship("Enrollment", back_populates="student")
    submissions = relationship("Submission", back_populates="student")

class Professor(Base):
    __tablename__ = "professors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)

    courses = relationship("Course", back_populates="professor")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    credits = Column(Integer, nullable=False)
    professor_id = Column(Integer, ForeignKey("professors.id"))

    professor = relationship("Professor", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)

    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_student_course'),)

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(100))
    max_score = Column(Integer)

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment")

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")

# Create tables
Base.metadata.create_all(bind=engine)

# ==========================================
# Pydantic Schemas
# ==========================================
class StudentBase(BaseModel):
    name: str
    email: str
    enrollment_year: int

class StudentCreate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CourseBase(BaseModel):
    title: str
    credits: int
    professor_id: Optional[int] = None

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    grade: Optional[float] = None

class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    grade: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class AverageGradeResponse(BaseModel):
    course_id: int
    average_grade: Optional[float]

# ==========================================
# FastAPI App Initialization
# ==========================================
app = FastAPI(title="University API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# Endpoints
# ==========================================

# EASY: 1. POST /students -> create a student
@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

# EASY: 2. GET /students/{id} -> retrieve a student
@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# MEDIUM: 1. POST /courses -> create a course with professor_id
@app.post("/courses", response_model=CourseResponse, status_code=201)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    if course.professor_id is not None:
        prof = db.query(Professor).filter(Professor.id == course.professor_id).first()
        if not prof:
            raise HTTPException(status_code=404, detail="Professor not found")
            
    new_course = Course(**course.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

# MEDIUM: 2. POST /enrollments -> enroll a student in a course
@app.post("/enrollments", response_model=EnrollmentResponse, status_code=201)
def create_enrollment(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    new_enrollment = Enrollment(**enrollment.model_dump())
    db.add(new_enrollment)
    
    try:
        db.commit()
        db.refresh(new_enrollment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student is already enrolled in this course")
        
    return new_enrollment

# HARD: 1. GET /courses/{id}/students -> list students enrolled in a course
@app.get("/courses/{course_id}/students", response_model=List[StudentResponse])
def get_course_students(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == course_id).all()
    return students

# HARD: 2. GET /courses/{id}/average-grade -> compute average grade for the course
@app.get("/courses/{course_id}/average-grade", response_model=AverageGradeResponse)
def get_course_average_grade(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    avg_grade = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == course_id).scalar()
    
    return AverageGradeResponse(
        course_id=course_id,
        average_grade=round(avg_grade, 2) if avg_grade is not None else None
    )
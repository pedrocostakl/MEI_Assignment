from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UniqueConstraint, func, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime

# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./university.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    enrollment_year = Column(Integer, nullable=False)
    enrollments = relationship("Enrollment", back_populates="student")

class Professor(Base):
    __tablename__ = "professors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    courses = relationship("Course", back_populates="professor")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    professor_id = Column(Integer, ForeignKey("professors.id"))
    professor = relationship("Professor", back_populates="courses")
    enrollments = relationship("Enrollment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float)
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String)
    max_score = Column(Integer)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    score = Column(Float)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# --- SCHEMAS ---
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    enrollment_year: int

class StudentResponse(StudentCreate):
    id: int
    class Config:
        from_attributes = True

class CourseCreate(BaseModel):
    title: str
    credits: int
    professor_id: int

class CourseResponse(CourseCreate):
    id: int
    class Config:
        from_attributes = True

class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    grade: Optional[float] = None

class EnrollmentResponse(EnrollmentCreate):
    id: int
    class Config:
        from_attributes = True

# --- API ---
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# EASY: CRUD
@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_student = Student(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# MEDIUM: Relationships
@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    professor = db.query(Professor).filter(Professor.id == course.professor_id).first()
    if not professor:
        # Note: In a real app, you'd ensure professors exist first. 
        # For this standalone, we check but assume DB integrity.
        raise HTTPException(status_code=404, detail="Professor not found")
    new_course = Course(**course.dict())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@app.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    # Check if student and course exist
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not student or not course:
        raise HTTPException(status_code=404, detail="Student or Course not found")
    
    # Check for existing enrollment
    existing = db.query(Enrollment).filter_by(student_id=enrollment.student_id, course_id=enrollment.course_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")

    new_enrollment = Enrollment(**enrollment.dict())
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

# HARD: Query + Aggregation
@app.get("/courses/{id}/students", response_model=List[StudentResponse])
def get_course_students(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == id).all()
    return students

@app.get("/courses/{id}/average-grade")
def get_course_average(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    avg_grade = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == id, Enrollment.grade != None).scalar()
    
    return {
        "course_id": id,
        "course_title": course.title,
        "average_grade": avg_grade if avg_grade is not None else 0.0
    }
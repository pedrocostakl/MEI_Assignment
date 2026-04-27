from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.sql import func
from typing import List, Optional
from datetime import datetime

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./university.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- SQLAlchemy Models ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
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
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)

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

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class StudentCreate(BaseModel):
    name: str
    email: str
    enrollment_year: int

class StudentOut(BaseModel):
    id: int
    name: str
    email: str
    enrollment_year: int
    
    model_config = ConfigDict(from_attributes=True)

class CourseCreate(BaseModel):
    title: str
    credits: int
    professor_id: int

class CourseOut(BaseModel):
    id: int
    title: str
    credits: int
    professor_id: int
    
    model_config = ConfigDict(from_attributes=True)

class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    grade: Optional[float] = None

class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    grade: Optional[float]

    model_config = ConfigDict(from_attributes=True)

class AverageGradeOut(BaseModel):
    course_id: int
    average_grade: Optional[float]

# --- FastAPI App ---
app = FastAPI(title="University API")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

# EASY
@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students/{id}", response_model=StudentOut)
def get_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

# MEDIUM
@app.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    # Optional check if professor exists
    professor = db.query(Professor).filter(Professor.id == course.professor_id).first()
    if not professor:
        # Note: If professors table is empty, course creation might fail here. 
        # For strict schema adherence, we check foreign key validity.
        raise HTTPException(status_code=400, detail="Professor not found")

    new_course = Course(**course.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@app.post("/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_student(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == enrollment.student_id,
        Enrollment.course_id == enrollment.course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")

    new_enrollment = Enrollment(**enrollment.model_dump())
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

# HARD
@app.get("/courses/{id}/students", response_model=List[StudentOut])
def get_course_students(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == id).all()
    return students

@app.get("/courses/{id}/average-grade", response_model=AverageGradeOut)
def get_course_average_grade(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    average = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == id).scalar()
    
    return AverageGradeOut(course_id=id, average_grade=average)
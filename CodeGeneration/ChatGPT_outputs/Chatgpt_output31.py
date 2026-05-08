# main.py

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    UniqueConstraint,
    DateTime,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# =========================
# Database Setup
# =========================

DATABASE_URL = "sqlite:///./university.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# =========================
# Models
# =========================

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
    grade = Column(Float)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uix_student_course"),
    )

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


# =========================
# Pydantic Schemas
# =========================

class StudentCreate(BaseModel):
    name: str
    email: str
    enrollment_year: int


class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    enrollment_year: int

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    title: str
    credits: int
    professor_id: Optional[int] = None


class CourseResponse(BaseModel):
    id: int
    title: str
    credits: int
    professor_id: Optional[int]

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    grade: Optional[float] = None


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    grade: Optional[float]

    class Config:
        from_attributes = True


class AverageGradeResponse(BaseModel):
    course_id: int
    average_grade: Optional[float]


# =========================
# Dependency
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# FastAPI App
# =========================

app = FastAPI(title="University API")


# =========================
# EASY ENDPOINTS
# =========================

@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing_student = db.query(Student).filter(Student.email == student.email).first()

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_student = Student(
        name=student.name,
        email=student.email,
        enrollment_year=student.enrollment_year,
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


@app.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


# =========================
# MEDIUM ENDPOINTS
# =========================

@app.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    if course.professor_id is not None:
        professor = (
            db.query(Professor)
            .filter(Professor.id == course.professor_id)
            .first()
        )

        if not professor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Professor not found",
            )

    new_course = Course(
        title=course.title,
        credits=course.credits,
        professor_id=course.professor_id,
    )

    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return new_course


@app.post(
    "/enrollments",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def enroll_student(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    course = db.query(Course).filter(Course.id == enrollment.course_id).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == enrollment.student_id,
            Enrollment.course_id == enrollment.course_id,
        )
        .first()
    )

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already enrolled in this course",
        )

    new_enrollment = Enrollment(
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        grade=enrollment.grade,
    )

    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)

    return new_enrollment


# =========================
# HARD ENDPOINTS
# =========================

@app.get(
    "/courses/{id}/students",
    response_model=List[StudentResponse],
)
def get_students_in_course(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    students = (
        db.query(Student)
        .join(Enrollment, Student.id == Enrollment.student_id)
        .filter(Enrollment.course_id == id)
        .all()
    )

    return students


@app.get(
    "/courses/{id}/average-grade",
    response_model=AverageGradeResponse,
)
def get_course_average_grade(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    average_grade = (
        db.query(func.avg(Enrollment.grade))
        .filter(Enrollment.course_id == id)
        .scalar()
    )

    return {
        "course_id": id,
        "average_grade": round(average_grade, 2) if average_grade is not None else None,
    }
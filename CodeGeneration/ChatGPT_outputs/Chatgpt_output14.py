from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, UniqueConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# ------------------------
# MODELS
# ------------------------

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
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="unique_enrollment"),)

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float)

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
    submitted_at = Column(String, default=str(datetime.utcnow()))


# ------------------------
# SCHEMAS
# ------------------------

class StudentCreate(BaseModel):
    name: str
    email: str
    enrollment_year: int


class StudentResponse(StudentCreate):
    id: int

    class Config:
        orm_mode = True


class CourseCreate(BaseModel):
    title: str
    credits: int
    professor_id: Optional[int]


class CourseResponse(CourseCreate):
    id: int

    class Config:
        orm_mode = True


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    grade: Optional[float]

    class Config:
        orm_mode = True


# ------------------------
# DB DEPENDENCY
# ------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------
# APP INIT
# ------------------------

app = FastAPI()
Base.metadata.create_all(bind=engine)

# ------------------------
# EASY ENDPOINTS
# ------------------------

@app.post("/students", response_model=StudentResponse, status_code=201)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.dict())
    db.add(db_student)
    try:
        db.commit()
        db.refresh(db_student)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    return db_student


@app.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# ------------------------
# MEDIUM ENDPOINTS
# ------------------------

@app.post("/courses", response_model=CourseResponse, status_code=201)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    if course.professor_id:
        professor = db.query(Professor).filter(Professor.id == course.professor_id).first()
        if not professor:
            raise HTTPException(status_code=404, detail="Professor not found")

    db_course = Course(**course.dict())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@app.post("/enrollments", response_model=EnrollmentResponse, status_code=201)
def enroll_student(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()

    if not student or not course:
        raise HTTPException(status_code=404, detail="Student or Course not found")

    db_enrollment = Enrollment(**enrollment.dict())
    db.add(db_enrollment)
    try:
        db.commit()
        db.refresh(db_enrollment)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")

    return db_enrollment


# ------------------------
# HARD ENDPOINTS
# ------------------------

@app.get("/courses/{id}/students", response_model=List[StudentResponse])
def get_students_in_course(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    students = (
        db.query(Student)
        .join(Enrollment)
        .filter(Enrollment.course_id == id)
        .all()
    )

    return students


@app.get("/courses/{id}/average-grade")
def get_average_grade(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    avg = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == id).scalar()

    return {
        "course_id": id,
        "average_grade": round(avg, 2) if avg is not None else None
    }
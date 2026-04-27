from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./school.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLite Foreign Key Support
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# --- SQLAlchemy Models ---
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
    submitted_at = Column(TIMESTAMP, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="submissions")


# --- Create Tables ---
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

class CourseBase(BaseModel):
    title: str
    credits: int
    professor_id: int

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class EnrollmentBase(BaseModel):
    student_id: int
    course_id: int
    grade: Optional[float] = None

class EnrollmentCreate(EnrollmentBase):
    pass

class EnrollmentResponse(EnrollmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI App ---
app = FastAPI(title="University API")

# --- Endpoints ---

# EASY 1: POST /students -> create a student
@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.model_dump())
    try:
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student with this email already exists.")

# EASY 2: GET /students/{id} -> retrieve a student
@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student

# MEDIUM 1: POST /courses -> create a course with professor_id
@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    db_course = Course(**course.model_dump())
    try:
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return db_course
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Foreign key violation: Professor ID may not exist.")

# MEDIUM 2: POST /enrollments -> enroll a student in a course
@app.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    db_enrollment = Enrollment(**enrollment.model_dump())
    try:
        db.add(db_enrollment)
        db.commit()
        db.refresh(db_enrollment)
        return db_enrollment
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig).lower()
        if "unique" in error_msg:
            raise HTTPException(status_code=400, detail="Student is already enrolled in this course.")
        raise HTTPException(status_code=400, detail="Foreign key violation: Student or Course ID may not exist.")

# HARD 1: GET /courses/{id}/students -> list students enrolled in a course
@app.get("/courses/{course_id}/students", response_model=List[StudentResponse])
def get_course_students(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    students = (
        db.query(Student)
        .join(Enrollment)
        .filter(Enrollment.course_id == course_id)
        .all()
    )
    return students

# HARD 2: GET /courses/{id}/average-grade -> compute average grade for the course
@app.get("/courses/{course_id}/average-grade")
def get_course_average_grade(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    result = (
        db.query(func.avg(Enrollment.grade))
        .filter(Enrollment.course_id == course_id)
        .scalar()
    )
    
    return {"course_id": course_id, "average_grade": result}
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
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from typing import Optional, List

DATABASE_URL = "sqlite:///./school.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()


# =========================
# Database Models
# =========================

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    enrollment_year = Column(Integer, nullable=False)

    enrollments = relationship("Enrollment", back_populates="student")


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


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="unique_enrollment"),
    )

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


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


# Create tables
Base.metadata.create_all(bind=engine)


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


# =========================
# Endpoints
# =========================

# 1. POST /students
@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing_student = (
        db.query(Student).filter(Student.email == student.email).first()
    )

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
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


# 2. GET /students/{id}
@app.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


# 3. POST /courses
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


# 4. POST /enrollments
@app.post(
    "/enrollments",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def enroll_student(
    enrollment: EnrollmentCreate,
    db: Session = Depends(get_db),
):
    student = (
        db.query(Student)
        .filter(Student.id == enrollment.student_id)
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    course = (
        db.query(Course)
        .filter(Course.id == enrollment.course_id)
        .first()
    )

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


# 5. GET /courses/{id}/students
@app.get("/courses/{id}/students", response_model=List[StudentResponse])
def get_course_students(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    students = (
        db.query(Student)
        .join(Enrollment)
        .filter(Enrollment.course_id == id)
        .all()
    )

    return students


# 6. GET /courses/{id}/average-grade
@app.get("/courses/{id}/average-grade")
def get_course_average_grade(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    enrollments = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == id,
            Enrollment.grade.isnot(None),
        )
        .all()
    )

    if not enrollments:
        return {
            "course_id": id,
            "average_grade": None,
            "message": "No grades available",
        }

    average = sum(e.grade for e in enrollments) / len(enrollments)

    return {
        "course_id": id,
        "average_grade": round(average, 2),
    }
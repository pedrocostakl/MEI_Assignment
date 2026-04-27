from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, ConfigDict
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

    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='_student_course_uc'),)

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
    submitted_at = Column(String) 

# Create tables
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

# --- FastAPI App Setup ---
app = FastAPI(title="School API")

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

# EASY: 1. POST /students
@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.email == student.email).first()
    if db_student:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_student = Student(**student.model_dump())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

# EASY: 2. GET /students/{id}
@app.get("/students/{id}", response_model=StudentResponse)
def read_student(id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == id).first()
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

# MEDIUM: 1. POST /courses
@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    new_course = Course(**course.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

# MEDIUM: 2. POST /enrollments
@app.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    db_course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    db_enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == enrollment.student_id,
        Enrollment.course_id == enrollment.course_id
    ).first()
    
    if db_enrollment:
        raise HTTPException(status_code=400, detail="Student is already enrolled in this course")

    new_enrollment = Enrollment(**enrollment.model_dump())
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

# HARD: 1. GET /courses/{id}/students
@app.get("/courses/{id}/students", response_model=List[StudentResponse])
def read_course_students(id: int, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == id).all()
    return students

# HARD: 2. GET /courses/{id}/average-grade
@app.get("/courses/{id}/average-grade")
def get_course_average_grade(id: int, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    avg_grade = db.query(func.avg(Enrollment.grade)).filter(
        Enrollment.course_id == id,
        Enrollment.grade.isnot(None)
    ).scalar()
    
    return {
        "course_id": id, 
        "average_grade": round(avg_grade, 2) if avg_grade is not None else 0.0
    }
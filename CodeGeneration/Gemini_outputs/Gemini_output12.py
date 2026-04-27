from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict
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
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=True)
    
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uix_student_course'),)
    
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
    professor_id: Optional[int] = None

class CourseOut(BaseModel):
    id: int
    title: str
    credits: int
    professor_id: Optional[int]
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Endpoints ---

@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.model_dump())
    db.add(db_student)
    try:
        db.commit()
        db.refresh(db_student)
        return db_student
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

@app.get("/students/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@app.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    if course.professor_id is not None:
        prof = db.query(Professor).filter(Professor.id == course.professor_id).first()
        if not prof:
            raise HTTPException(status_code=400, detail="Professor not found")
            
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.post("/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll_student(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")
        
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=400, detail="Course not found")

    db_enrollment = Enrollment(**enrollment.model_dump())
    db.add(db_enrollment)
    try:
        db.commit()
        db.refresh(db_enrollment)
        return db_enrollment
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student already enrolled in this course")

@app.get("/courses/{course_id}/students", response_model=List[StudentOut])
def get_course_students(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == course_id).all()
    return students

@app.get("/courses/{course_id}/average-grade", response_model=AverageGradeOut)
def get_course_average_grade(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    avg_grade = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == course_id).scalar()
    
    return {"course_id": course_id, "average_grade": avg_grade}
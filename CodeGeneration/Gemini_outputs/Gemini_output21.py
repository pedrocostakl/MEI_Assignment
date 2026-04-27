from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./school.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SQLAlchemy Models ---
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
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
    professor_id: Optional[int] = None

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

class AverageGradeResponse(BaseModel):
    average_grade: Optional[float]

# --- Initialization ---
Base.metadata.create_all(bind=engine)
app = FastAPI(title="University API")

# --- Endpoints ---

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

@app.get("/students/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    if course.professor_id:
        professor = db.query(Professor).filter(Professor.id == course.professor_id).first()
        if not professor:
            raise HTTPException(status_code=400, detail="Professor not found")
    new_course = Course(**course.model_dump())
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

@app.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment(enrollment: EnrollmentCreate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == enrollment.student_id).first()
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")
    
    course = db.query(Course).filter(Course.id == enrollment.course_id).first()
    if not course:
        raise HTTPException(status_code=400, detail="Course not found")

    existing_enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == enrollment.student_id,
        Enrollment.course_id == enrollment.course_id
    ).first()
    if existing_enrollment:
        raise HTTPException(status_code=400, detail="Student is already enrolled in this course")

    new_enrollment = Enrollment(**enrollment.model_dump())
    db.add(new_enrollment)
    db.commit()
    db.refresh(new_enrollment)
    return new_enrollment

@app.get("/courses/{id}/students", response_model=List[StudentResponse])
def get_course_students(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_id == id).all()
    return students

@app.get("/courses/{id}/average-grade", response_model=AverageGradeResponse)
def get_course_average_grade(id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    avg_grade = db.query(func.avg(Enrollment.grade)).filter(Enrollment.course_id == id).scalar()
    
    return AverageGradeResponse(average_grade=avg_grade)
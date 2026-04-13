from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, NonNegativeInt, StringConstraints
from typing import Annotated
from database import sessionLocal, engine
import model

model.base.metadata.create_all(bind=engine)

app = FastAPI()

class Courses(BaseModel):
    id: int
    name:str
    description: Annotated[str, StringConstraints(min_length=10)]
    Fee_pkr:NonNegativeInt
    is_active:bool

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the Course API!"}

@app.post("/course/", response_model=Courses)
async def create_Course(course:Courses, db:Session = Depends(get_db)):
    db_course = db.query(model.DBcourse).filter(model.DBcourse.id == course.id).first()
    if db_course:
        raise HTTPException(status_code = 400, detail="This course already exists")
    
    new_course = model.DBcourse(
        id=course.id,
        name=course.name,
        description=course.description,
        Fee_pkr=course.Fee_pkr,
        is_active=course.is_active
        )
    
    db.add(new_course)
    db.commit()
    db.refresh(new_course)

    return new_course

@app.get("/course/{course_id}", response_model=Courses)
async def single_read(course_id:int, db:Session = Depends(get_db)):
    course = db.query(model.DBcourse).filter(model.DBcourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course

@app.delete("/course/{course_id}")
async def delete_course(course_id:int, db:Session = Depends(get_db)):
    course = db.query(model.DBcourse).filter(model.DBcourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    
    db.delete(course)
    db.commit()

    return {"message": "Course deleted successfully."}

@app.get("/course/", response_model=list[Courses])
async def read_all_courses(active_only:bool = False, db:Session = Depends(get_db)):
    if active_only:
        courses = db.query(model.DBcourse).filter(model.DBcourse.is_active == True).all()
    else:
        courses = db.query(model.DBcourse).all()
    
    return courses
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, NonNegativeInt, StringConstraints
from typing import List, Annotated

CRUDapp = FastAPI()

class courseS(BaseModel):
    id: int
    name: str
    description: Annotated[str, StringConstraints(min_length=10)]
    fee_pkr: NonNegativeInt
    is_active: bool

courSes_db: List[courseS] = []

@CRUDapp.get("/")
async def root():
    return {"message": "Welcome to the Course API!"}

@CRUDapp.post("/courses/", response_model=courseS)
async def create_course(course: courseS):
    for existing_course in courSes_db:
        if existing_course.id == course.id:
            raise HTTPException(status_code = 400, detail="This course already exists.")
    
    courSes_db.append(course)
    return course

# For retrieving all courses, with an optional query parameter to filter active courses
@CRUDapp.get("/courses/", response_model=List[courseS])
async def read_course(active_only: bool = False):
    if active_only:
        return [course for course in courSes_db if course.is_active]
    return courSes_db

@CRUDapp.put("/courses/{course_id}", response_model=courseS)
async def update_course(course_id: int, updated_course: courseS):
    for index, existing_course in enumerate(courSes_db):
        if existing_course.id == course_id:
            courSes_db[index] = updated_course
            return updated_course
        
    raise HTTPException(status_code=404, detail="Course not Found.")

@CRUDapp.delete("/courses/{course_id}")
async def delete_course(course_id: int):
    for index, existing_course in enumerate(courSes_db):
        if existing_course.id == course_id:
            courSes_db.pop(index)
            return {"message": "Course deleted successfully."}
    
    raise HTTPException(status_code=404, detail="Course not found.")


# For single course retrieval
@CRUDapp.get("/courses/{course_id}", response_model=courseS)
async def single_course(course_id:int):
    for course in courSes_db:
        if course.id == course_id:
            return course

    raise HTTPException(status_code=404, detail="Course not Found.")
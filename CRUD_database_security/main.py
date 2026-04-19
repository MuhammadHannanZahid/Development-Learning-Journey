from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, NonNegativeInt, StringConstraints, ConfigDict
from typing import Annotated
from database import sessionLocal, engine
import model
from security import hash_password, verify_password, create_access_token, verify_access_token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

model.base.metadata.create_all(bind=engine)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

class Courses(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name:str
    description: Annotated[str, StringConstraints(min_length=10)]
    Fee_pkr:NonNegativeInt
    is_active:bool

class UserCreate(BaseModel):
    username:str
    password:Annotated[str, StringConstraints(min_length=8)]

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    username:str
    is_admin:bool

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    try:
        payload = verify_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    user = db.query(model.DBuser).filter(model.DBuser.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found.")
    
    return user

@app.get("/")
async def root():
    return {"message": "Welcome to the Course API!"}

@app.post("/course/", response_model=Courses)
async def create_Course(course:Courses, db:Session = Depends(get_db), current_user: model.DBuser = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can create courses.")
    
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
async def delete_course(course_id:int, db:Session = Depends(get_db), current_user: model.DBuser = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can delete courses.")

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

@app.put("/course/{course_id}", response_model=Courses)
async def update_course(course_id:int, updated_course:Courses, db:Session = Depends(get_db), current_user: model.DBuser = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only administrators can update courses.")

    course = db.query(model.DBcourse).filter(model.DBcourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    course.name = updated_course.name
    course.description = updated_course.description
    course.Fee_pkr = updated_course.Fee_pkr
    course.is_active = updated_course.is_active

    db.commit()
    db.refresh(course)
    return course

@app.post("/register/", response_model = UserResponse)
async def register_user(user:UserCreate, db:Session = Depends(get_db)):
    username_check = db.query(model.DBuser).filter(model.DBuser.username == user.username).first()
    if username_check:
        raise HTTPException(status_code=400, detail="Username already registered.")
    else:
        if user.password:
            hashed_password = hash_password(user.password)
        else:
            raise HTTPException(status_code=400, detail="Password is required.")
        
        db_user = model.DBuser(username=user.username, hash=hashed_password)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
@app.post("/login/")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):
    db_user = db.query(model.DBuser).filter(model.DBuser.username == form_data.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    
    if not verify_password(form_data.password, db_user.hash):
        raise HTTPException(status_code=400, detail="Invalid username or password.")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}
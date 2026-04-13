from sqlalchemy import Column, Integer, String, Boolean
from database import base

class DBcourse(base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index = True)
    name = Column(String, index=True)
    description = Column(String)
    Fee_pkr = Column(Integer)
    is_active = Column(Boolean, default=True)
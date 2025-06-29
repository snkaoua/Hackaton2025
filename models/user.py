from sqlalchemy import Column, Integer, String
from app.db.session import engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    user_id = Column(Integer, nullable=True)

Base.metadata.create_all(bind=engine)
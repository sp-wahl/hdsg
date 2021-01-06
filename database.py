from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy_utils import create_database, database_exists

from config import Config


def verify_password(plain_password, hashed_password):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

class HasVotedMetadata(BaseModel):
    ballot_box_id: str
    running_number: int


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    username = Column(String(200), unique=True, primary_key=True)
    hashed_password = Column(String(200))


class Voter(Base):
    __tablename__ = "voters"
    number = Column(String(100), unique=True, primary_key=True)
    name = Column(String(500))
    voted = Column(Boolean, default=False)
    notes = Column(String(500))
    ballot_box_id = Column(String(100))
    running_number = Column(Integer, default=None)
    timestamp = Column(String(100), default=None)
    user_id = Column(String(200), ForeignKey("users.username", ondelete="SET NULL"))
    user = relationship("User")


class DBHelper:
    def __init__(self):
        self.connection_str = Config.DB_CONNECTION_STRING
        self._session = None

    def __enter__(self):
        if self._session:
            return self._session
        if not database_exists(self.connection_str):
            create_database(self.connection_str)
        engine = create_engine(self.connection_str)

        Base.metadata.create_all(engine)

        self._session = Session(engine)
        return self._session

    def __exit__(self, type, value, traceback):
        self._session.close()
        self._session = None

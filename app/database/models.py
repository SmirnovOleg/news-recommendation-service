import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import relationship

Base: DeclarativeMeta = declarative_base()


class UserRole(str, Enum):
    CLIENT = 'client'
    ADMIN = 'admin'


class User(Base):
    __tablename__ = 'User'

    id = Column(Integer, primary_key=True)

    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    role = Column(String, nullable=False, default=UserRole.CLIENT)


class Post(Base):
    __tablename__ = 'Post'

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('User.id'))

    header = Column(String, nullable=False)
    photo = Column(LargeBinary, nullable=True)
    text = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    author = relationship('User')


class Comment(Base):
    __tablename__ = 'Comment'

    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('User.id'))
    post_id = Column(Integer, ForeignKey('Post.id'))

    text = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    author = relationship('User')
    post = relationship('Post')

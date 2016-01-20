import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Track(Base):
    __tablename__ = 'track'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    path = Column(String(250), nullable=False)
    performer = Column(Integer, ForeignKey('performer.id'))

class Performer(Base):
    __tablename__ = 'performer'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    sort_name = Column(String(80), nullable=False)

engine = create_engine('sqlite:///music_player.db')

Base.metadata.create_all(engine)

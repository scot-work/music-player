import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date
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
    album = Column(Integer, ForeignKey('album.id'))
    track_number = Column(Integer)
    rating = Column(Integer)
    times_played = Column(Integer)
    last_played = Column(Date)
    transitions_to = Column(Integer)

class Album(Base):
    __tablename__ = 'album'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    year = Column(Integer)
    performer = Column(Integer, ForeignKey('performer.id'))
    genre_id = Column(Integer, ForeignKey('genre.id'))

class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)

class Performer(Base):
    __tablename__ = 'performer'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    sort_name = Column(String(80), nullable=False)
    albums = relationship('Album', backref="album")

engine = create_engine('sqlite:///music_player.db')

Base.metadata.create_all(engine)

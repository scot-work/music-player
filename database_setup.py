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
    genre = Column(Integer, ForeignKey('genre.id'))
    tracks = relationship('Track', backref="track")

class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    #albums = relationship('Album', backref="album")

class Performer(Base):
    __tablename__ = 'performer'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    sort_name = Column(String(80), nullable=False)
    albums = relationship('Album', backref="album")

class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

class Tag_Track(Base):
    __tablename__ = 'tag_track'

    id = Column(Integer, primary_key=True)
    tag = Column(Integer, ForeignKey('tag.id'))
    track = Column(Integer, ForeignKey('track.id'))

class Membership(Base):
    __tablename__ = 'membership'

    id = Column(Integer, primary_key=True)
    p_individual = Column(Integer, ForeignKey('performer.id'))
    p_group = Column(Integer, ForeignKey('performer.id'))

engine = create_engine('sqlite:///music_player.db')

Base.metadata.create_all(engine)

from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, exists, and_
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Track, Performer, Album
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import os
import json
import string

app = Flask(__name__)

# Set up database
engine = create_engine('sqlite:///music_player.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Home page
@app.route('/')
def home():
    return render_template('home.html')
    pass

# Play a playlist
@app.route('/playlist/play/')
def playlist():
    playlist_name = request.args.get('list')
    playlist_path = 'playlists/' + playlist_name
    with open(playlist_path) as data_file:
        data = json.load(data_file)
    return render_template('playlist.html', data = data)
    pass

# List tracks
@app.route('/track/')
def listTracks():
    tracks = session.query(Track).order_by(Track.title)
    return render_template('listTracks.html',
        tracks = tracks)
    pass

# Track Details
@app.route('/track/<int:track_id>')
def trackDetails(track_id):
    track = session.query(Track).filter_by(id = track_id).one()
    album = session.query(Album).filter_by(id = track.album).one()
    performer = session.query(Performer).filter_by(id = track.performer).one()
    return render_template('trackDetails.html', track = track,
        album = album,
        performer = performer)

# List performers
@app.route('/performer/')
def listPerformers():
    performers = session.query(Performer).order_by(Performer.sort_name)
    return render_template('listPerformers.html',
        performers = performers)
    pass

# Create a new performer
@app.route('/performer/new/', methods=['GET', 'POST'])
def newPerformer():
    if request.method == 'POST':
        newPerformer = Performer(name = request.form['name'],
            sort_name = request.form['sort_name'])
        session.add(newPerformer)
        session.commit()
        return redirect(url_for('listPerformers'))
    else:
        return render_template('newPerformer.html')

# Edit a performer
@app.route('/performer/<int:performer_id>/edit/', methods=['GET', 'POST'])
def editPerformer(performer_id):
    editedPerformer = session.query(Performer).filter_by(id=performer_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedPerformer.name = request.form['name']
            editedPerformer.sort_name = request.form['sort_name']
            return redirect(url_for('listPerformers'))
    else:
        return render_template(
            'editPerformer.html', performer = editedPerformer)

# Delete a performer
@app.route('/performer/<int:performer_id>/delete/', methods=['GET', 'POST'])
def deletePerformer(performer_id):
    performerToDelete = session.query(
        Performer).filter_by(id = performer_id).one()
    if request.method == 'POST':
        session.delete(performerToDelete)
        session.commit()
        return redirect(
            url_for('listPerformers', performer_id = performer_id))
    else:
        return render_template(
            'deletePerformer.html', performer = performerToDelete)

# Browse file system
@app.route('/browse/')
def browseFiles():
    path = request.args.get('path')
    if not path:
        path = '/Users/scotclose/Development/repositories/music-player/static'
    file_list = os.listdir(path)
    path_components = string.split(path, '/')
    return render_template('browseFiles.html',
        current_path = path,
        files = file_list,
        path_components = path_components,
        working_path = '/')

# Get ID3 info for a track
@app.route('/track_info/')
def trackInfo():
    path = request.args.get('path')
    audio = MP3(path, ID3=EasyID3)
    return render_template('showID3Info.html', audio = audio)

# Scan for tracks
@app.route('/scan/')
def scan():
    path = request.args.get('path')
    artist_set = set()
    album_set = set()
    recurse(path, artist_set, album_set)
    return render_template('scanResults.html',
        artists = sorted(artist_set),
        albums = album_set)

def recurse(path, artist_set, album_set):
    print "Scanning path " + path
    file_list = os.listdir(path)
    for file in file_list:
        if file.endswith('.mp3'):
            audio = MP3(path + '/' + str(file), ID3 = EasyID3)
            if not 'title' in audio:
                print "title tag not found"
            else:
                track_title = audio['title'][0]

            # Get performer/artist
            if not 'artist' in audio:
                print "artist tag not found"
            else:
                performer_name = audio['artist'][0]
                artist_set.add(audio['artist'][0])
                #if session.query(exists().where(Performer.name == performer_name)).scalar():
                performer = session.query(Performer).filter_by(name = performer_name).one()
                if performer:
                    print performer_name + " already exists"
                    performer_id = performer.id
                else:
                    newPerformer = Performer(name = performer_name,
                        sort_name = performer_name)
                    performer_id = newPerformer.id
                    session.add(newPerformer)
                    session.commit()

            # Get album
            if not 'album' in audio:
                print "album tag not found"
            else:
                track_album = audio['album'][0]
                print track_album
                album_set.add(track_album)
                #if session.query(exists().where(Album.title == album_title)).scalar():
                album = session.query(Album).filter_by(title = track_album).one()
                if album:
                    print "album " + track_album + " already exists"
                    album_id = album.id
                else:
                    newAlbum = Album(title = track_album)
                    album_id = newAlbum.id
                    session.add(newAlbum)
                    session.commit()

            if not 'tracknumber' in audio:
                print "track number not found"
                track_number = 0
            else:
                track_number = audio['tracknumber'][0]
            # Check for duplicate
            track_query = session.query(Track).filter(and_(Track.title == track_title,
                Track.album == track_album))
            print str(track_query.count()) + " rows"
            if (track_query.count() > 0):
                print "Track already exists: " + track_title
            else:
              # Create track
                newTrack = Track(title = track_title,
                    album = album_id,
                    path = path + '/' + str(file),
                    performer = performer_id,
                    track_number = track_number)
                session.add(newTrack)
                session.commit()

        if os.path.isdir(path + '/' + str(file)):
            recurse(path + '/' + file, artist_set, album_set)

def showAsLink(path, file):
    if not file.startswith('.'):
        if os.path.isdir(path + '/' + file):
            return True
        else:
            #print("not a dir: " + path + '/' + file)
            return False
    else:
        return False
app.jinja_env.filters['showAsLink'] = showAsLink

def showAsFile(file):
    if (file.endswith('.m4a') or file.endswith('.mp3')):
        return True
    else:
        return False
app.jinja_env.filters['showAsFile'] = showAsFile

def isNotEmptyString(s):
    if s:
        return True
    else:
        return False
app.jinja_env.filters['isNotEmptyString'] = isNotEmptyString

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)

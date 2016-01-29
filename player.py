from flask import Flask, render_template, request, redirect, url_for, jsonify
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

# List tracks
@app.route('/track/')
def listTracks():
    tracks = session.query(Track).order_by(Track.title)
    return render_template('listTracks.html',
        tracks = tracks)

# Track Details
@app.route('/track/<int:track_id>')
def trackDetails(track_id):
    track = session.query(Track).filter_by(id = track_id).one()
    album = session.query(Album).filter_by(id = track.album).one()
    performer = session.query(Performer).filter_by(id = track.performer).one()
    return render_template('trackDetails.html', track = track,
        album = album,
        performer = performer)


# Edit a track
@app.route('/track/<int:track_id>/edit/', methods = ['GET', 'POST'])
def editTrack(track_id):
    editedTrack = session.query(Track).filter_by(id = track_id).one()
    if request.method == 'POST':
        if request.form['title']:
            editedTrack.title = request.form['title']
            print "title"
        if request.form['performer']:
            editedTrack.performer = request.form['performer']
            print "performer"
        if request.form['album']:
            editedTrack.album = request.form['album']
        if request.form['track_number']:
            editedTrack.track_number = request.form['track_number']
        if request.form['rating']:
            editedTrack.rating = request.form['rating']
        if request.form['path']:
            editedTrack.path = request.form['path']
        if request.form['transitions_to']:
            editedTrack.transitions_to = request.form['transitions_to']
            print "transitions to"
        session.add(editedTrack)
        session.commit()
        return redirect(url_for('listTracks'))
    else:
        return render_template(
            'editTrack.html', track = editedTrack)

# Delete a track
@app.route('/track/<int:track_id>/delete/', methods=['GET', 'POST'])
def deleteTrack(track_id):
    trackToDelete = session.query(Track).filter_by(id = track_id).one()
    if request.method == 'POST':
        session.delete(trackToDelete)
        session.commit()
        return redirect(
            url_for('listTracks', track_id = track_id))
    else:
        return render_template(
            'deleteTrack.html', track = trackToDelete)

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
        if request.form['sort_name']:
            editedPerformer.sort_name = request.form['sort_name']
        session.add(editedPerformer)
        session.commit()
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

# Show albums
@app.route('/album/')
def listAlbums():
    # albums = session.query(Album).order_by(Album.performer).all()
    # session.query(User).join(Address, User.id==Address.user_id)
    albums = session.query(Album).all()
    print albums
    return render_template('listAlbums.html', albums = albums)

@app.route('/album/<int:album_id>/')
def albumDetails(album_id):
    album = session.query(Album).filter_by(id = album_id).one()
    album_tracks = session.query(Track).filter_by(album
        = album_id).order_by(Track.track_number)
    return render_template('albumDetails.html', album = album,
        tracks = album_tracks)

@app.route('/album/<int:album_id>/play/')
def playAlbum(album_id):
    album = session.query(Album).filter_by(id = album_id).one()
    album_tracks = session.query(Track).filter_by(album
        = album_id).order_by(Track.track_number)
    return render_template('playAlbum.html', tracks = album_tracks,
        album_title = album.title)

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

@app.route('/_ajax_test')
def test():
    track = request.args.get('track')
    return jsonify(result = track + " was played ")

def recurse(path, artist_set, album_set):
    print "Scanning path " + path
    file_list = os.listdir(path)
    for file in file_list:
        if file.endswith('.mp3'):

            # Get ID3 tags from track
            audio = MP3(path + '/' + str(file), ID3 = EasyID3)

            # date
            if not 'date' in audio:
                print "date tag not found"
                track_date = 9999
            else:
                track_date = audio['date'][0]

            # title
            if not 'title' in audio:
                print "title tag not found"
                track_title = "untitled"
            else:
                track_title = audio['title'][0]

            # artist
            if not 'artist' in audio:
                print "artist tag not found"
                performer_name = "unknown"
            else:
                performer_name = audio['artist'][0]

            artist_set.add(performer_name)

            # Album
            if not 'album' in audio:
                track_album = "unknown"
            else:
                track_album = audio['album'][0]
            album_set.add(track_album)

            # Track Number
            if not 'tracknumber' in audio:
                track_number = 0
            else:
                track_number = audio['tracknumber'][0]

            # Add to database



            # Find out if this performer is already in the db
            performer = session.query(Performer).filter_by(name
                = performer_name).first()
            if performer:
                # already in db
                performer_id = performer.id
            else:
                # add to db
                newPerformer = Performer(name = performer_name,
                    sort_name = performer_name)
                session.add(newPerformer)
                session.commit()
                performer_id = newPerformer.id

            # TODO Check for performer to eliminate duplicate album titles (II)
            album_query = session.query(Album).filter(and_
                (Album.title == track_album,
                Album.performer == performer_id))

            if (album_query.count() > 0):
                album = album_query.first()
                album_id = album.id
            else:
                album = Album(
                    title = track_album,
                    year = track_date,
                    performer = performer_id)
                session.add(album)
                session.commit()
                album_id = album.id

            # Check for duplicate
            track_query = session.query(Track).filter(and_
                (Track.title == track_title,
                Track.album == album.id))
            if (not track_query.count() > 0):
              # Create track
                newTrack = Track(title = track_title,
                    album = album_id,
                    path = localPath(path + '/' + str(file)),
                    performer = performer_id,
                    track_number = track_number)
                session.add(newTrack)
                session.commit()

        if os.path.isdir(path + '/' + str(file)):
            recurse(path + '/' + file, artist_set, album_set)

def localPath(absolute_path):
    path_start = absolute_path.index("/static")
    # path_start = absolute_path.indexOf("/static")
    # return absolute_path.substring(path_start)
    # remove &#39;, replace with '
    result = absolute_path[path_start:]
    # result.replace("&#39;", "'")
    return result

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


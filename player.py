from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Track, Performer
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
    tracks = session.query(Track)
    performer = session.query(Performer).one()
    return render_template('tracks.html',
        tracks = tracks,
        performer = performer)
    pass

# List performers
@app.route('/performer/')
def listPerformers():
    performers = session.query(Performer).order_by(Performer.sort_name)
    return render_template('performer.html',
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

# Delete a performer
@app.route('/performer/<int:performer_id>/delete/', methods=['GET', 'POST'])
def deletePerformer(performer_id):
    performerToDelete = session.query(
        Performer).filter_by( id = performer_id).one()
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
    if file.endswith('.mp3'):
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


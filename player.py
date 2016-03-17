from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, exists, and_
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Track, Performer, Album, Tag, Tag_Track, Membership, Preferences
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import os, random, json, string, datetime, operator
from datetime import timedelta
from random import randrange

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
@app.route('/tracks/')
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
        if request.form['performer']:
            editedTrack.performer = request.form['performer']
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
        # session.add(editedTrack)
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

# Play unrated tracks
@app.route('/track/unrated/')
def playUnratedTracks():
    track_list = session.query(Track).filter_by(rating = 0).limit(15)
    return render_template('playTracks.html', tracks = track_list)

# List performers
@app.route('/performer/')
@app.route('/performers/')
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
    editedPerformer = session.query(Performer).filter_by(
        id = performer_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedPerformer.name = request.form['name']
        if request.form['sort_name']:
            editedPerformer.sort_name = request.form['sort_name']
        # session.add(editedPerformer)
        session.commit()
        return redirect(url_for('listPerformers'))
    else:
        return render_template(
            'editPerformer.html', performer = editedPerformer)

@app.route('/performer/<int:performer_id>/tag/', methods = ['GET', 'POST'])
def tagAllPerformerTracks(performer_id):
    performer_to_tag = session.query(Performer).filter_by(
                id = performer_id).one()
    if request.method == 'POST':
        if request.form['tags']:
            # Get performer from database

            # Get list of albums
            albums = performer_to_tag.albums
            # Get selected tags
            tags_to_add = request.form.getlist('tags')
            for tag in tags_to_add:
                for album in albums:
                    tracks = album.tracks
                    for track in tracks:
                        # Check for existing tags
                        tag_count = session.query(Tag_Track).filter(
                            and_(Tag_Track.tag == tag,
                            Tag_Track.track == track.id)).count()
                        if tag_count == 0:
                            tag_track = Tag_Track(tag = tag, track = track.id)
                            session.add(tag_track)
            session.commit()
        return redirect(
            url_for('listPerformers'))
    # Process GET
    else:
        # Get list of all tags
        tags = session.query(Tag).order_by(Tag.name).all()
        return render_template(
            'tagPerformer.html', performer = performer_to_tag, tags = tags)

# Delete a performer
@app.route('/performer/<int:performer_id>/delete/', methods = ['GET', 'POST'])
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

# Play all tracks by a performer
@app.route('/performer/<int:performer_id>/play/')
def playPerformer(performer_id):
    performer = session.query(Performer).filter_by(id = performer_id).one()
    related_performers = session.query(Membership).filter_by(
        p_group = performer.id)
    related_groups = session.query(Membership).filter_by(
        p_individual = performer.id)
    tracks = session.query(Track).filter_by(performer = performer_id).all()
    if related_performers:
        for related_performer in related_performers:
            print "Adding tracks from related individual %s" % related_performer.p_individual
            related_tracks = session.query(Track).filter_by(
                performer = related_performer.p_individual).all()
            tracks = tracks + related_tracks
    if related_groups:
        for related_group in related_groups:
            print "Adding tracks from related group %s" % related_group.p_group
            related_tracks = session.query(Track).filter_by(
                performer = related_group.p_group).all()
            tracks = tracks + related_tracks
    return render_template('playTracks.html', tracks = shuffle(tracks),
        album_title = performer.name)

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

# Show performers and albums
@app.route('/library/')
def listLibrary():
    performers = session.query(Performer).order_by(Performer.sort_name).all()
    return render_template('listLibrary.html', performers = performers)

# Show albums
@app.route('/album/')
@app.route('/albums/')
def listAlbums():
    albums = session.query(Album).order_by(Album.title).all()
    return render_template('listAlbums.html', albums = albums)

@app.route('/album/<int:album_id>/delete', methods=['GET', 'POST'])
def deleteAlbum(album_id):
    albumToDelete = session.query(
        Album).filter_by(id = album_id).one()
    if request.method == 'POST':
        session.delete(albumToDelete)
        session.commit()
        return redirect(
            url_for('listAlbums', album_id = album_id))
    else:
        return render_template(
            'deleteAlbum.html', album = albumToDelete)

@app.route('/album/<int:album_id>/edit', methods=['GET', 'POST'])
def editAlbum(album_id):
    albumToEdit = session.query(
        Album).filter_by(id = album_id).one()
    if request.method == 'POST':
        if request.form['title']:
            albumToEdit.title = request.form['title']
        # year
        if request.form['year']:
            albumToEdit.year = request.form['year']
        session.commit()
        return redirect(
            url_for('listAlbums', album_id = album_id))
    else:
        return render_template(
            'editAlbum.html', album = albumToEdit)

# Add a tag to every track in an album
@app.route('/album/<int:album_id>/tag', methods=['GET', 'POST'])
def tagAlbum(album_id):
    # Get album from database
    albumToEdit = session.query(
        Album).filter_by(id = album_id).one()
    # Get list of all tags
    tags = session.query(Tag).order_by(Tag.name).all()
    # Get list of album tracks
    tracks = albumToEdit.tracks
    # Process POST
    if request.method == 'POST':
        if request.form['tags']:
            # Get selected tags
            tags_to_add = request.form.getlist('tags')
            for tag in tags_to_add:
                for track in tracks:
                    # Check for existing tags
                    tag_count = session.query(Tag_Track).filter(
                        and_(Tag_Track.tag == tag,
                        Tag_Track.track == track.id)).count()
                    if tag_count == 0:
                        tag_track = Tag_Track(tag = tag, track = track.id)
                        session.add(tag_track)
            session.commit()
        return redirect(url_for('listAlbums'))
    # Process GET
    else:
        return render_template(
            'tagAlbum.html', album = albumToEdit, tags = tags)

@app.route('/album/<int:album_id>/')
def albumDetails(album_id):
    album = session.query(Album).filter_by(id = album_id).one()
    album_tracks = session.query(Track).filter_by(album
        = album_id).order_by(Track.track_number)
    return render_template('albumDetails.html', album = album,
        tracks = album_tracks)

# Pick a random album to play
@app.route('/album/random/')
def playRandomAlbum():
    albums_in_database = session.query(Album).count()
    found = False
    while found == False:
        random_index = randrange(0, albums_in_database)
        album_count = session.query(Album).filter_by(id = random_index).count()
        if album_count > 0:
            album = session.query(Album).filter_by(id = random_index).one()
            # Was this played recently?
            # Check the first track (this is a hack)
            track_one = album.tracks[0]
            if (not (wasPlayedRecently(track_one))):
                found = True
            else:
                print "Album played too recently: %s" % album.title
        else:
            print "random album not found"
            continue

    return redirect(url_for('playAlbum',
        album_id = random_index,
        random = True))

# Play an album
@app.route('/album/<int:album_id>/play/')
def playAlbum(album_id):
    # Get album based on ID
    try:
        album = session.query(Album).filter_by(id = album_id).one()
        # Get performer from DB
        performer = session.query(Performer).filter_by(id = album.performer).one()
        # Get album tracks in order
        album_tracks = session.query(Track).filter_by(album
            = album_id).order_by(Track.track_number)

        return render_template('playTracks.html',
            tracks = album_tracks,
            album_title = album.title,
            album_year = album.year,
            album_performer = performer.name,
            random = random)
    except:
        print "Invalid album id: %s" % album_id
        return redirect(url_for('playRandomAlbum'))

@app.route('/tag/')
@app.route('/tags/')
@app.route('/tag/list/')
def listTags():
    tags = session.query(Tag).order_by(Tag.name).all()
    return render_template('listTags.html', tags = tags)

@app.route('/tag/play/')
def playTags():
    tags = session.query(Tag).order_by(Tag.name).all()
    return render_template('playTags.html', tags = tags)

@app.route('/tag/new/', methods=['GET', 'POST'])
def newTag():
    if request.method == 'POST':
        newTag = Tag(name = request.form['name'])
        session.add(newTag)
        session.commit()
        return redirect(url_for('listTags'))
    else:
        return render_template('newTag.html')

# Get a list of tracks with a given tag
@app.route('/tag/<int:tag_id>/list/')
def listTagTracks(tag_id):
    tag_tracks = session.query(Tag_Track).filter_by(tag = tag_id).all()
    tag = session.query(Tag).filter_by(id = tag_id).one()
    track_list = []
    for tag_track in tag_tracks:
        try:
            track = session.query(Track).filter_by(id = tag_track.track).one()
            track_list.append(track)
        except:
            print "Error: No track found for tag %s" % tag_track
    return render_template('listTagTracks.html',
        tracks = track_list, tag = tag)

# Play tracks based on multiple selected tracks (tag A or tag B)
@app.route('/tags/play/', methods=['GET', 'POST'])
def playTagsTracks():
    if request.method == "POST":
        track_list = []
        to_remove = []
        mode = request.form['mode']
        print "Tag select mode is %s" % mode
        # Get tag IDs
        checked_list = request.form.getlist('selected_tags')
        if mode == "any":
        # Find all tracks with any of the selected tags (OR)
            # Repeat for each selected tag
            for tag_id in checked_list:
                tag_tracks = session.query(Tag_Track).filter_by(
                    tag = tag_id).all()
                for tag_track in tag_tracks:
                    try:
                        track = session.query(Track).filter_by(
                            id = tag_track.track).one()
                    except:
                        print "Error: Track not found %s" % tag_track.track
                        continue
                    # Check here for rating and last played
                    # rating = track.rating
                    if wasPlayedRecently(track):
                        pass
                    if ratingPass(track):
                        track_list.append(track)
        else:
        # Find only tracks with all of the selected tags
            # Repeat for each selected tag
            first_tag = True
            for tag_id in checked_list:
                tag_tracks = session.query(Tag_Track).filter_by(
                    tag = tag_id).all()
                if first_tag:
                    # add all to list
                    first_tag = False
                    for tag_track in tag_tracks:
                        try:
                            track = session.query(Track).filter_by(
                                id = tag_track.track).one()
                        except:
                            continue
                        if wasPlayedRecently(track):
                            pass
                        if ratingPass(track):
                            track_list.append(track)
                            print "Adding %s" % track.title
                else:
                    # Remove track if no match in tag_track
                    for track in track_list:
                        print "Checking %s" % track.title
                        found = False
                        for tag_track in tag_tracks:
                            if track.id == tag_track.track:
                                found = True
                                print "Match: %s" % track.title
                        if not found:
                            print "Removing %s" % track.title
                            to_remove.append(track)
            for track in to_remove:
                track_list.remove(track)
        # return render_template('playTracks.html', tracks = track_list)
        return render_template('playTracks.html', tracks = shuffle(track_list))

# Play all the tracks with the given tag
@app.route('/tag/<int:tag_id>/play/')
def playTagTracks(tag_id):
    tag_tracks = session.query(Tag_Track).filter_by(tag = tag_id).all()
    tag = session.query(Tag).filter_by(id = tag_id).one()
    track_list = []
    for tag_track in tag_tracks:
        try:
            track = session.query(Track).filter_by(id = tag_track.track).one()
        except:
            print "Error: Track not found %s" % tag_track.track
            continue
        # Check here for rating and last played
        # rating = track.rating
        if wasPlayedRecently(track):
            pass
        else:
            track_list.append(track)
    return render_template('playTracks.html', tracks = shuffle(track_list),
        album_title = tag.name)

@app.route('/tag/<int:tag_id>/track/<int:track_id>/remove/')
def removeTagFromTrack(tag_id, track_id):
    tagged_track = session.query(Tag_Track).filter(and_(
        Tag_Track.tag == tag_id, Tag_Track.track == track_id)).one()
    session.delete(tagged_track)
    session.commit()
    return redirect(url_for('listTagTracks', tag_id = tag_id))

@app.route('/membership/')
def listMembership():
    memberships = session.query(Membership).order_by(Membership.p_group).all()
    groups = []
    for membership in memberships:
        group = session.query(Performer).filter_by(
            id = membership.p_group).one()
        members = session.query(Performer).filter_by(
            id = membership.p_individual).all()
        groups.append(group.name)

    return render_template("listMemberships.html", memberships = groups)

# Create a new member/group relationship
@app.route('/membership/new/', methods=['GET', 'POST'])
def newMembership():
    if request.method == 'POST':
        if request.form['group']:
            if request.form['members']:
                group = request.form.get('group')
                members = request.form.getlist('members')
                for member in members:
                    print "Adding member %s to group %s" % (member, group)
                    # is this person already in the group?
                    count = session.query(Membership).filter(
                        and_(Membership.p_group == group,
                            Membership.p_individual == member)).count()
                    if count == 0:
                        # Add the person to the group
                        membership = Membership(p_individual = member,
                        p_group = group)
                        session.add(membership)
                    else:
                        print "Membership already exists"
            else: print "no members found"
        else:
            print "no group found"
        session.commit()
        memberships = session.query(Membership).all()
        return render_template(
            "listMemberships.html", memberships = memberships)
    else:
        # Need to send list of all performers
        performers = session.query(Performer).order_by(Performer.sort_name)
        return render_template('newMembership.html', performers = performers)

# Update preferences
@app.route('/preferences/', methods = ['GET', 'POST'])
def editPreferences():
    preferences = session.query(Preferences).filter_by(id = 1).one()
    if request.method == 'POST':
        if request.form['rating']:
            preferences.rating_minimum = request.form['rating']
        if request.form['recent']:
            preferences.recent_minimum = request.form['recent']
        session.commit()
        return render_template('home.html')
    if request.method == 'GET':
        print "Preferences: %s %s" % (preferences.rating_minimum, preferences.recent_minimum)
        return render_template('editPreferences.html', preferences = preferences)

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
    print "AJAX request received"
    message = request.args.get('message')
    return jsonify(result = str(message))

@app.route('/_ajax_edit_track')
def updateTrack():
    # Get the track ID from the AJAX request
    track_id = request.args.get('track_id')
    # Get the track object from the DB
    track = session.query(Track).filter_by(id = track_id).one()
    # Get tags associated with this track
    selected_tags_query = session.query(Tag_Track).filter_by(
        track = track.id).all()
    # Get all available tags
    all_tags_query = session.query(Tag).order_by(Tag.name).all()
    all_tags = {}
    for tag in all_tags_query:
        all_tags[tag.id] = tag.name
    selected_tags = {}
    for tag in selected_tags_query:
        tag_name_query = session.query(Tag).filter_by(id = tag.tag).one()
        selected_tags[tag.tag] = tag_name_query.name

    json_response = {}
    json_response['title'] = track.title
    json_response['track_number'] = track.track_number
    json_response['rating'] = track.rating
    json_response['times_played'] = track.times_played
    json_response['last_played'] = str(track.last_played)
    # json_response['all_tags'] = all_tags
    json_response['all_tags'] = sorted(all_tags.items(),
        key = operator.itemgetter(1))

    # print json_response['all_tags']
    json_response['selected_tags'] = selected_tags
    # print (json_response)
    return jsonify(json_response)

# Save changes to the database
@app.route('/_ajax_save_track')
def saveTrack():
    changed = False
    # Get track ID from AJAX request
    track_id = request.args.get('track_id')
    # Get the track from the DB
    track = session.query(Track).filter_by(id = track_id).one()
    # Get new title
    new_title = request.args.get('track_title')
    if (new_title != track.title):
        changed = True
        track.title = new_title
    # Get new track number
    new_number = request.args.get('track_number')
    if (new_number != track.track_number):
        changed = True
        track.track_number = new_number
    # Get new rating
    new_rating = request.args.get('track_rating')
    if (new_rating != track.rating):
        changed = True
        track.rating = new_rating
    # track.rating = rating
    new_tags = json.loads(request.args.get('track_tags'))
    # print "Length: %s " % len(new_tags)[0]
    if (new_tags[0]):
        for tag in new_tags[0]:
            tag_query = session.query(Tag_Track).filter(and_(
                Tag_Track.track == track_id,
                Tag_Track.tag == tag)).count()
            # print "Found %s rows for tag %s " % (tag_query, tag)
            if tag_query == 0:
                # print "New tag"
                tag_track = Tag_Track(tag = tag, track = track_id)
                session.add(tag_track)
        session.commit()

    if (changed):
        # session.add(track)
        session.commit()
    return jsonify(response = "Track saved")

# Update track played history
@app.route('/_ajax_track_played/')
def trackPlayed():
    track_id = request.args.get('track_id')
    track = session.query(Track).filter_by(id = track_id).one()
    track.last_played = datetime.datetime.now()
    track.times_played = track.times_played + 1
    # print "updating track history for %s" % track.title
    session.commit()
    return jsonify(response = "Updated track history")

# Scan a directory for music files
def recurse(path, artist_set, album_set):
    file_list = os.listdir(path)
    for file in file_list:
        if file.endswith('.mp3'):
            # TODO include other filetypes (mp4?. ogg?)
            # Get ID3 tags from track
            audio = MP3(path + '/' + str(file), ID3 = EasyID3)

            try:
                cover_src = File(path + '/' + str(file)).tags['APIC:'].data
                cover_dest = path + '/' + 'cover.jpg'
                with open(cover_dest, 'wb') as img:
                    img.write(cover_src)
            except:
                pass
                #print "No cover art found for %s" % path

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
                # get the first number up to the /
                track_number = string.split(audio['tracknumber'][0], '/')[0]

            # Find out if this performer is already in the db
            performer = session.query(Performer).filter_by(name
                = performer_name).first()
            if performer:
                # already in db
                performer_id = performer.id
            else:
                # add to db
                new_performer = Performer(name = performer_name,
                    sort_name = performer_name)
                session.add(new_performer)
                session.commit()
                performer = session.query(Performer).filter_by(name
                    = performer_name).first()
                performer_id = performer.id

            # Find out if album is in database
            album_query = session.query(Album).filter(and_
                (Album.title == track_album,
                Album.performer == performer_id))

            if (album_query.count() > 0):
                album = album_query.first()
                album_id = album.id
            else:
                # Add album to database
                album = Album(
                    title = track_album,
                    year = track_date,
                    performer = performer_id)
                session.add(album)
                session.commit()
                album_id = album.id

            # Check for duplicates
            track_query = session.query(Track).filter(and_
                (Track.title == track_title,
                Track.album == album.id))
            if (not track_query.count() > 0):
                # Create track
                newTrack = Track(title = track_title,
                    album = album_id,
                    path = localPath(path + '/' + str(file)),
                    performer = performer_id,
                    track_number = track_number,
                    rating = 0,
                    times_played = 0)
                session.add(newTrack)
                session.commit()
        if os.path.isdir(path + '/' + str(file)):
            recurse(path + '/' + file, artist_set, album_set)

def localPath(absolute_path):
    # TODO: clean up special characters?
    path_start = absolute_path.index("/static")
    result = absolute_path[path_start:]
    return result

def showAsLink(path, file):
    if not file.startswith('.'):
        if os.path.isdir(path + '/' + file):
            return True
        else:
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

# Was this track played recently?
def wasPlayedRecently(track):
    # minimum_days = 14
    minimum_days = session.query(Preferences).filter_by(id = 1).one().recent_minimum
    if track.last_played:
        difference = datetime.datetime.now().date() - track.last_played
        recent_limit = timedelta(days = minimum_days) # TODO: Need to store this in the database, not hard-coded
        if (difference < recent_limit):
            return True
    return False

# Does this track suck?
def ratingPass(track):
    # minimum_rating = 3
    minimum_rating = session.query(Preferences).filter_by(id = 1).one().rating_minimum
    if track.rating == 0:
        # not yet rated
        return True
    if track.rating < minimum_rating:
        return False
    return True

# Shuffle playlist (Fisher-Yates)
def shuffle(tracks):
    random.seed()
    track_count = len(tracks) - 1
    for remaining_tracks in range(track_count, 0, -1):
        random_track = random.randint(0, remaining_tracks)
        if random_track == remaining_tracks:
            continue # No point in swapping with same track
        tracks[remaining_tracks], tracks[random_track] = \
        tracks[random_track], tracks[remaining_tracks]
    return tracks

app.jinja_env.filters['isNotEmptyString'] = isNotEmptyString

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)


#!/usr/bin/env python3
import functools

from flask import Flask, render_template, redirect, request, flash
from flask_login import LoginManager, current_user, login_required, logout_user, login_user
from flask_socketio import SocketIO, disconnect, emit
from peewee import DoesNotExist, SqliteDatabase

from config import SECRET_KEY, MOPIDY_HOST, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DEBUG, DB, LDAP_HOST, \
    MAX_OPEN_REQUESTS, VOTES_TO_PLAY, VOTES_TO_SKIP, SITE_NAME
from models import db_init, User, SongRequest, Vote
from mopidy import Mopidy
from utils import ldap_auth

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins=[])
login_manager = LoginManager()
login_manager.init_app(app)


def ws_login_required(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)

    return wrapped


def message(msg: str, alert: str = 'info', broadcast: bool = False):
    socketio.emit('msg', {'class': alert, 'msg': msg}, broadcast=broadcast)


@app.route("/")
def index():
    return render_template('music.html', site_name=SITE_NAME)


@socketio.on('refresh')
def mopidy_refresh():
    track = mopidy.get_current_track()
    if track:
        emit('track', {
            'title': track['name'],
            'artists': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'art': track['art']
        })
    else:
        emit({})
    tracks = []
    for i in range(10):
        if not i:
            tracks.append(mopidy.next_track())
        else:
            tracks.append(mopidy.next_track(tracks[i - 1]))
    emit('tracks', tracks)
    emit('requests', [r.to_dict() for r in SongRequest.select().filter(done=False)])


@socketio.on('search')
@ws_login_required
def search(data):
    if data.get('query'):
        results = mopidy.search(data['query'])
        try:
            results = results['result'][0]['tracks'][:15]
            emit('search results', results)
        except KeyError:
            pass


@socketio.on('request')
@ws_login_required
def request_song(data):
    if current_user.admin:
        mopidy.play_song_next(data['uri'])
        message('Song has been admin queued.', 'success')
    else:
        if len(current_user.unplayed_requests()) >= MAX_OPEN_REQUESTS:
            message('Too many open requests.', 'danger')
            return
        s, created = SongRequest.get_or_create(uri=data['uri'],
                                               defaults={
                                                   'user': current_user.id,
                                               })
        if created:
            song = mopidy.lookup(data['uri'])
            s.title = song['name']
            s.artist = song['artists'][0]['name']
            s.save()
        message('Requested "{}" by "{}"'.format(s.title, s.artist), 'success')


@socketio.on('vote')
@ws_login_required
def do_vote(data):
    vote_type = data['vote']
    try:
        song = SongRequest.get(uri=data['uri'])
    except DoesNotExist:
        message('Song does not exist', 'danger')
        return
    if song.user is current_user:
        message('Cannot vote for own request', 'warning')
        return
    if not current_user.admin:
        vote, created = Vote.get_or_create(user=current_user.id, song=song)
        if vote_type == 'upvote' and not vote.value == 1:
            vote.value = 1
            song.votes += 1
        elif vote_type == 'downvote' and not vote.value == -1:
            vote.value = -1
            song.votes -= 1
        else:
            message('Invalid vote', 'danger')
            return
        vote.save()
    if song.votes >= VOTES_TO_PLAY or current_user.admin:
        mopidy.play_song_next(song.uri)
        song.done = True
        message('"{}" was queued'.format(song.title), 'info')
    elif song.votes <= VOTES_TO_SKIP or current_user.admin:
        song.done = True
        message('"{}" was voted off the island'.format(song.title), 'info')
    else:
        message('Voted for "{}" by "{}"'.format(song.title, song.artist), 'success')
    song.save()


@socketio.on('admin')
@ws_login_required
def mopidy_ws(data):
    if not current_user.admin:
        message('Insufficient permissions', 'danger')
        disconnect()
    action = data.pop('action')
    s = True
    if action == 'play':
        mopidy.play()
    elif action == 'playlist':
        mopidy.stop()
        mopidy.add_track(data['uri'])
    elif action == 'pause':
        mopidy.pause()
    elif action == 'next':
        mopidy.next()
    elif action == 'prev':
        mopidy.previous()
    elif action == 'volup':
        s = mopidy.fade(4)
    elif action == 'voldown':
        s = mopidy.fade(-4)
    elif action == 'fadedown':
        s = mopidy.fade(-20)
    elif action == 'fadeup':
        s = mopidy.fade(20)
    else:
        message('Invalid action', 'danger')
        return
    if not s:
        message('Failed to retrieve volume; cowardly refusing to set volume', 'danger')
        return
    message('Success', 'success')


@login_manager.user_loader
def load_user(user_id):
    return User.get(id=user_id)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    created = False
    try:
        user = User.get(username=username)
    except DoesNotExist:
        if LDAP_HOST:
            user = ldap_auth(username, password)
            created = True
    if user:
        if created or user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
    if not user:
        flash('Invalid credentials.')
    return redirect('/')


# This hook ensures that a connection is opened to handle any queries
# generated by the request.
@app.before_request
def _db_connect():
    if not type(DB) == SqliteDatabase:
        DB.connect()


# This hook ensures that the connection is closed when we've finished
# processing the request.
@app.teardown_request
def _db_close(exc):
    if not type(DB) == SqliteDatabase:
        if not DB.is_closed():
            DB.close()


if __name__ == "__main__":
    db_init()
    mopidy = Mopidy(MOPIDY_HOST, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    socketio.run(app, debug=DEBUG)

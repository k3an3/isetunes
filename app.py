#!/usr/bin/env python3
import functools
from time import sleep

from flask import Flask, render_template, redirect, request, flash
from flask_login import LoginManager, current_user, login_required, logout_user, login_user
from flask_socketio import SocketIO, disconnect, emit
from markupsafe import escape
from peewee import DoesNotExist, SqliteDatabase

from config import SECRET_KEY, DB, LDAP_HOST, \
    MAX_OPEN_REQUESTS, VOTES_TO_PLAY, VOTES_TO_SKIP, SITE_NAME, PROVIDER, PLAYER
from models import User, SongRequest, Vote
from utils import ldap_auth

try:
    provider = PROVIDER
except ImportError:
    print("Error! Configure a provider in config_local.py")
    raise SystemExit

try:
    player = PLAYER
except ImportError:
    print("Error! Configure a player in config_local.py")

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
    emit('msg', {'class': alert, 'msg': escape(msg)}, broadcast=broadcast)


@app.route("/")
def index():
    return render_template('music.html', site_name=SITE_NAME)


@socketio.on('refresh')
def player_refresh():
    track = player.get_current_track()
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
            tracks.append(player.next_track())
        else:
            tracks.append(player.next_track(tracks[i - 1]))
    emit('tracks', tracks)
    emit('requests', [r.to_dict() for r in SongRequest.select().filter(done=False)])


@socketio.on('search')
@ws_login_required
def search(data):
    if data.get('query'):
        results = provider.search(data['query'])
        emit('search results', results)


@socketio.on('request')
@ws_login_required
def request_song(data):
    if current_user.admin:
        player.play_song_next(data['uri'])
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
            song = provider.lookup(data['uri'])
            s.title = song['name']
            s.artist = ", ".join([a['name'] for a in song['artists']])
            s.save()
            message('Requested "{}" by "{}"'.format(s.title, s.artist), 'success')
        else:
            message('Song was already requested!', 'warning')


@socketio.on('vote')
@ws_login_required
def do_vote(data):
    vote_type = data['vote']
    try:
        song = SongRequest.get(uri=data['uri'])
    except DoesNotExist:
        message('Song does not exist', 'danger')
        return
    if song.user.id == current_user.id:
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
    if vote_type == 'upvote' and (song.votes >= VOTES_TO_PLAY or current_user.admin):
        player.play_song_next(song.uri, soon=not current_user.admin)
        song.done = True
        message('"{}" was queued'.format(song.title), 'info')
    elif vote_type == 'downvote' and (song.votes <= VOTES_TO_SKIP * -1 or current_user.admin):
        song.done = True
        message('"{}" was voted off the island'.format(song.title), 'info')
    else:
        message('Voted for "{}" by "{}"'.format(song.title, song.artist), 'success')
    song.save()


@socketio.on('admin')
@ws_login_required
def player_ws(data):
    if not current_user.admin:
        message('Insufficient permissions', 'danger')
        disconnect()
    action = data.pop('action')
    s = True
    if action == 'play':
        player.play()
    elif action == 'playlist':
        player.stop()
        sleep(0.3)
        player.clear()
        sleep(0.3)
        player.add_track(data['uri'])
        sleep(0.3)
        player.play()
        sleep(0.3)
        player.set_consume()
    elif action == 'pause':
        player.pause()
    elif action == 'next':
        player.next()
    elif action == 'prev':
        player.previous()
    elif action == 'volup':
        s = player.fade(4)
    elif action == 'voldown':
        s = player.fade(-4)
    elif action == 'fadedown':
        s = player.fade(-20)
    elif action == 'fadeup':
        s = player.fade(20)
    else:
        message('Invalid action', 'danger')
        return
    if not s:
        message('Failed to retrieve volume; cowardly refusing to set volume', 'danger')
        return
    message('Success', 'success')


@socketio.on('chat')
def chat(data):
    admin = ' (admin)' if current_user.admin else ''
    emit('chat msg', {'username': escape(current_user.username) + admin,
                      'message': escape(data['message'][:80])
                      }, broadcast=True)


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

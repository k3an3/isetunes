import json

from flask import Flask, render_template
from flask_socketio import SocketIO, disconnect, emit

from config import SECRET_KEY, MOPIDY_HOST, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DEBUG
from mopidy import UNAUTH_COMMANDS, Mopidy

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)


@app.route("/")
def hello():
    return render_template('music.html')


@socketio.on('mopidy', namespace='/mopidy')
def mopidy_ws(data, **kwargs):
    auth = kwargs.pop('auth', False)
    action = data.pop('action')
    if not auth and action not in UNAUTH_COMMANDS:
        print("Disconnected client from Mopidy endpoint, not authorized/invalid command")
        disconnect()
    if action == 'search':
        results = mopidy.search(**data)
        try:
            results = results['result'][0]['tracks']
            emit('search results', json.dumps(results))
        except Exception as e:
            pass
    elif action == 'add_track':
        r = mopidy.add_track(**data)
    elif action == 'get_current_track':
        track = mopidy.get_current_track()
        emit('track', json.dumps({
            'title': track['name'],
            'artists': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'art': track['art']
        }))


if __name__ == "__main__":
    mopidy = Mopidy(MOPIDY_HOST, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    socketio.run(app, debug=DEBUG)

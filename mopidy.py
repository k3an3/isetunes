"""
mopidy.py
~~~~~~~~~

Websocket JSONRPC client for the Mopidy media server
"""
import json
from time import sleep

import requests
from requests.auth import HTTPBasicAuth

UNAUTH_COMMANDS = (
    'search',
    'get_tracks',
    'add_track',
    'get_state',
    'get_current_track',
    'get_time_position',
)

SPOTIFY_API = 'https://api.spotify.com/v1/{}'


class Spotify:
    def __init__(self, client_id, client_secret):
        self.token = self.auth(client_id, client_secret)

    def spotify_get(self, query):
        return requests.get(SPOTIFY_API.format(query), headers={'Authorization': 'Bearer ' + self.token}).json()

    def auth(self, cid, cs):
        data = {
            'grant_type': 'client_credentials'
        }
        r = requests.post('https://accounts.spotify.com/api/token',
                         data=data,
                         auth=HTTPBasicAuth(cid, cs))
        return r.json().get('access_token')

    def get_album_art(self, album_id, image=1):
        r = self.spotify_get('albums/' + album_id)['images'][image]['url']
        return r


class Mopidy:
    def __init__(self, host, client_id=None, client_secret=None):
        self.host = "http://" + host + ":6680/mopidy/rpc"
        self.id = 1
        self.spotify = None
        if client_id and client_secret:
            self.spotify = Spotify(client_id, client_secret)
        self.song = None

    def send(self, method, **kwargs):
        msg = {"jsonrpc": "2.0", "id": self.id, 'method': method, 'params': dict(kwargs)}
        return requests.post(self.host, data=json.dumps(msg)).json()

    def get_current_track(self):
        try:
            song = self.send('core.playback.get_current_tl_track')['result']['track']
        except TypeError:
            return None
        if not self.song or not song['uri'] == self.song['uri']:
            self.song = song
            if self.spotify:
                self.song['art'] = self.spotify.get_album_art(song['album']['uri'].split(':')[2])
            else:
                self.song['art'] = '/static/album.png'
        return self.song

    def get_state(self):
        return self.send('core.playback.get_state')

    def get_time_position(self):
        return self.send('core.playback.get_time_position')

    def get_volume(self):
        return int(self.send('core.mixer.get_volume')['result'])

    def set_volume(self, volume: int):
        return self.send('core.mixer.set_volume', volume=volume)

    def fade(self, change: int, delay: int = 0.2):
        current_volume = self.get_volume()
        end_volume = current_volume + change
        for i in range(current_volume, end_volume, 1 if change > 0 else -1):
            if 0 < i > 100:
                break
            self.set_volume(i)
            sleep(delay)

    def next(self):
        return self.send('core.playback.next')

    def pause(self):
        return self.send('core.playback.pause')

    def play(self, track=None):
        return self.send('core.playback.play', tl_track=track)

    def previous(self):
        return self.send('core.playback.previous')

    def clear(self):
        return self.send('core.tracklist.clear')

    def resume(self):
        return self.send('core.playback.resume')

    def stop(self):
        return self.send('core.playback.stop')

    def get_playlists(self):
        return self.send('core.playlists.as_list')

    def add_track(self, uri):
        return self.send('core.tracklist.add', uri=uri)

    def get_tracks(self):
        return self.send('core.tracklist.get_tracks')['result']

    def get_tracklist_length(self):
        return self.send('core.tracklist.get_length')['result']

    def search(self, query):
        return self.send('core.library.search', any=[query])

    def custom(self, target, key, value):
        if value == 'true':
            value = True
        elif value == 'false':
            value = False
        return self.send(target, **{key: value})

    # Broken; don't use
    def get_images(self, uris, index=0):
        return self.send('core.library.get_images', uris=uris)['result'].popitem()[1][index]

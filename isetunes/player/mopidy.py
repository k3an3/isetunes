import json
import random
from time import sleep, time

import requests

from isetunes.player import Player
from isetunes.provider import Provider

UNAUTH_COMMANDS = (
    'search',
    'get_tracks',
    'queue',
    'get_state',
    'get_current_track',
    'get_time_position',
)

# Tune to reduce load on Mopidy server
MOPIDY_REFRESH_SECS = 5


class Mopidy(Player):
    def __init__(self, host, provider: Provider):
        self.host = "http://" + host + "/mopidy/rpc"
        self.id = 1
        self.provider = None
        self.provider = provider
        self.song = None
        self.updated = 0
        self.tracks = []

    def send(self, method: str, **kwargs):
        msg = {"jsonrpc": "2.0", "id": self.id, 'method': method, 'params': dict(kwargs)}
        return requests.post(self.host, data=json.dumps(msg)).json()

    def get_upcoming(self, count: int = 10):
        tracks = []
        for i in range(count):
            if not i:
                tracks.append(self.next_track())
            else:
                tracks.append(self.next_track(tracks[i - 1]))
        return tracks

    def get_current_track(self):
        if time() - self.updated >= MOPIDY_REFRESH_SECS:
            self.updated = time()
            try:
                song = self.send('core.playback.get_current_tl_track')['result']['track']
            except TypeError:
                return None
            if not self.song or not song['uri'] == self.song['uri']:
                self.song = song
                if self.provider:
                    self.song['art'] = self.provider.get_album_art(song['album']['uri'].split(':')[2])
                else:
                    self.song['art'] = '/static/album.png'
        return self.song

    def get_state(self):
        return self.send('core.playback.get_state')

    def get_time_position(self):
        return self.send('core.playback.get_time_position')

    def get_volume(self):
        vol = self.send('core.mixer.get_volume')['result']
        if vol:
            return int(vol)
        return 0

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
        return end_volume

    def next(self):
        return self.send('core.playback.next')

    def pause(self):
        return self.send('core.playback.pause')

    def play(self, track: str = None):
        return self.send('core.playback.play', tl_track=track)

    def previous(self):
        return self.send('core.playback.previous')

    def clear(self):
        return self.send('core.tracklist.clear')

    def resume(self):
        return self.send('core.playback.resume')

    def stop(self):
        return self.send('core.playback.stop')

    def move(self, start: int, end: int, position: int):
        return self.send('core.tracklist.move', start=start, end=end, to_position=position)

    def get_playlists(self):
        return self.send('core.playlists.as_list')

    def queue(self, uri: str, position: int = None):
        return self.send('core.tracklist.add', uris=[uri], at_position=position)

    def play_song_next(self, uri: str, soon=False):
        self.queue(uri=uri)
        length = self.get_tracklist_length()
        return self.move(length - 1, length, random.randint(1, 10) if soon else 1)

    def get_tracks(self):
        return self.send('core.tracklist.get_tracks')['result']

    def get_tracklist_length(self):
        return self.send('core.tracklist.get_length')['result']

    def search(self, query: str):
        return self.send('core.library.search', any=[query])

    def lookup(self, uri: str):
        return self.send('core.library.search', uri=uri)['result'][0]['tracks'][0]

    def next_track(self, tl_track: str = None):
        return self.send('core.tracklist.next_track', tl_track=tl_track)['result']

    def set_consume(self, consume: bool = True):
        return self.send('core.tracklist.set_consume', value=consume)

    def custom(self, target, key, value):
        if value == 'true':
            value = True
        elif value == 'false':
            value = False
        return self.send(target, **{key: value})

    # Broken; don't use
    def get_images(self, uris, index=0):
        return self.send('core.library.get_images', uris=uris)['result'].popitem()[1][index]

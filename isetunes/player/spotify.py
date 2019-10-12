import json
import os
import time
from typing import Dict
from urllib.parse import urlparse

import requests

from isetunes.player import Player
from isetunes.provider import Provider

API_URL = 'https://api.spotify.com/v1/me/'


class SpotifyPlayer(Player):
    def __init__(self, spotify: Provider):
        self.spotify = spotify
        auth = None
        if os.path.exists('auth.json'):
            with open('auth.json', 'r') as infile:
                auth = json.load(infile)
        self.auth(spotify.cid, spotify.cs, auth)

    # https://github.com/eclair4151/Local-Spotify-Web-Connect-Api-Python
    @staticmethod
    def auth(client_id: str, client_secret: str, code: str = None):
        payload = {'redirect_uri': 'http://localhost',
                   'client_id': client_id,
                   'client_secret': client_secret
                   }

        if code is None:
            scopes = ["user-modify-playback-state", "user-read-playback-state", "playlist-read-private",
                      "playlist-read-collaborative", "streaming"]

            print()
            print()
            print("Go to the following url, and after clicking ok, copy and paste the link you are redirected to from "
                  "your browser starting with 'localhost'\n")
            print(
                "https://accounts.spotify.com/authorize/?client_id=" + client_id + "&response_type=code&redirect_uri"
                                                                                   "=http://localhost&scope=" +
                "%20".join(
                    scopes))

            url = input("\nPaste localhost url: ")
            parsed_url = urlparse(url)
            payload['grant_type'] = 'authorization_code'
            payload['code'] = parsed_url.query.split('=')[1]
            auth_code = {}

        else:
            payload['grant_type'] = 'refresh_token'
            payload['refresh_token'] = code["refresh_token"]

        result = requests.post("https://accounts.spotify.com/api/token", data=payload)

        response_json = result.json()
        cur_seconds = time.time()
        auth_code['expires_at'] = cur_seconds + response_json["expires_in"] - 60
        auth_code['access_token'] = response_json["access_token"]

        if "refresh_token" in response_json:
            auth_code['refresh_token'] = response_json["refresh_token"]

        with open('auth.json', 'w') as outfile:
            json.dump(auth_code, outfile)
        return auth_code

    # https://github.com/eclair4151/Local-Spotify-Web-Connect-Api-Python
    def _auth_header(self):
        with open('auth.json', 'r') as infile:
            auth = json.load(infile)
        if time.time() > auth["expires_at"]:
            auth = self.auth(auth)
        return {"Authorization": "Bearer " + auth["access_token"]}

    def _put(self, path: str, data: Dict = {}, params: Dict = {}):
        return requests.put(API_URL + path, params=params,
                            headers=self._auth_header(),
                            json=data)

    def _get(self, path: str, params: Dict = {}):
        return requests.put(API_URL + path, params=params,
                            headers=self._auth_header())

    def get_volume(self):
        return self._get('player/volume')

    def set_volume(self):
        pass

    def get_state(self):
        pass

    def play(self, data: str = None):
        data = {'context_uri': data}
        return self._put('player/play', data=data)

    def pause(self):
        return self._put('player/pause')

    def next(self):
        pass

    def previous(self):
        pass

    def stop(self):
        pass

    def queue(self):
        pass

    def play_next(self):
        pass

    def get_current_track(self):
        pass


"""
# Sets the volume from 0-100 of the currently active device
# A device_id can be specified to set the volume of a specific device
def set_device_volume(volume, device_id=None):
    headers = get_valid_auth_header()
    params = {'volume_percent': volume}
    if device_id is not None:
        params['device_id'] = device_id

    response = requests.put("https://api.spotify.com/v1/me/player/volume", headers=headers, params=params)
    print(response)


def get_playlists(limit=None, offset=None):
    headers = get_valid_auth_header()
    params = {}
    if limit is not None:
        params['limit'] = limit

    if offset is not None:
        params['offset'] = offset
    return requests.get("https://api.spotify.com/v1/me/playlists", headers=headers).json()


if not os.path.isfile('auth.json'):
    auth = authorize()

### The following code will take the first playlist on the account and start playing it on the first available connected device
# devices = get_devices()
# playlists = get_playlists()
#
# first_playlist_uri = playlists['items'][0]['uri']
# first_device_id = devices['devices'][0]['id']
# play_on_device(device_id=first_device_id, context_uri=first_playlist_uri)

### how to pause music or set the volume of an active device
# set_device_volume(30)
# pause_active_music()

# print('')
"""

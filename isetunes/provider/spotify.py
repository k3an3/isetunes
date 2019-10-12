import requests
from requests.auth import HTTPBasicAuth

from isetunes.provider import Provider

SPOTIFY_API = 'https://api.spotify.com/v1/{}'


class Spotify(Provider):
    def __init__(self, client_id: str, client_secret: str):
        self.token = self.auth(client_id, client_secret)
        self.cid = client_id
        self.cs = client_secret
        if not self.token:
            raise Exception("Spotify Auth Failed!!!")

    def get(self, query: str) -> str:
        return requests.get(SPOTIFY_API.format(query), headers={'Authorization': 'Bearer ' + self.token}).json()

    def auth(self, cid: str, cs: str) -> str:
        data = {
            'grant_type': 'client_credentials'
        }
        r = requests.post('https://accounts.spotify.com/api/token',
                          data=data,
                          auth=HTTPBasicAuth(cid, cs))
        return r.json().get('access_token')

    def get_album_art(self, album_id: str, image: int = 1):
        r = self.get('albums/' + album_id)['images'][image]['url']
        return r

    def search(self, query: str, limit: int = 15):
        return self.get('search?type=track&limit={}&q={}'.format(limit, query))['tracks']['items']

    def lookup(self, uri: str):
        return self.get('tracks/' + uri.split(':')[-1])

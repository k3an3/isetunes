from peewee import SqliteDatabase

SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
MOPIDY_HOST = ''

"""
Configure a Provider and player in config_local.py!!!
Example:
from isetunes import provider, player
PROVIDER = provider.Spotify(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
PLAYER = player.SpotifyPlayer(PROVIDER)
"""

SITE_NAME = 'ISETunes'
SECRET_KEY = 'something long and random'
DEBUG = False
DB = SqliteDatabase('db.sql')

try:
    from config_local import *
except ImportError:
    pass

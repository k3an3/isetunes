SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
MOPIDY_HOST = ''
SECRET_KEY = 'something long and random'
DEBUG = False

try:
    from config_local import *
except ImportError:
    pass

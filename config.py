from peewee import SqliteDatabase

SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
MOPIDY_HOST = ''
SITE_NAME = 'Mopidy-Demo'
SECRET_KEY = 'something long and random'
DEBUG = False
DB = SqliteDatabase('db.sql')
LDAP_HOST = ''
LDAP_BASE_DN = ''
LDAP_PORT = 389
LDAP_SSL = False
VOTES_TO_PLAY = 3
VOTES_TO_SKIP = 3
MAX_OPEN_REQUESTS = 5

try:
    from config_local import *
except ImportError:
    pass

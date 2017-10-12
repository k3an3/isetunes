from peewee import SqliteDatabase

SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
MOPIDY_HOST = ''
SECRET_KEY = 'something long and random'
DEBUG = False
DB = SqliteDatabase('db.sql')
LDAP_HOST = ''
LDAP_BASE_DN = ''
LDAP_PORT = 389
LDAP_SSL = False

try:
    from config_local import *
except ImportError:
    pass

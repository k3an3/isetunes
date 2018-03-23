from flask_login import UserMixin
from passlib.handlers.sha2_crypt import sha256_crypt
from peewee import Model, OperationalError, CharField, BooleanField, ForeignKeyField, IntegerField
from redis import StrictRedis

from config import DB

redis = StrictRedis(decode_responses=True)


def db_init():
    DB.connect()
    try:
        DB.create_tables([User])
        print('Creating tables...')
    except OperationalError:
        pass
    DB.close()


class BaseModel(Model):
    class Meta:
        database = DB


class User(BaseModel, UserMixin):
    username = CharField(unique=True)
    password = CharField(null=True)
    admin = BooleanField(default=False)
    ldap = BooleanField(default=False)

    def check_password(self, password: str) -> bool:
        if self.ldap:
            from utils import ldap_auth
            return ldap_auth(self.username, password)
        return sha256_crypt.verify(password, self.password)

    def set_password(self, password: str) -> None:
        self.password = sha256_crypt.encrypt(password)

    def unplayed_requests(self):
        return self.requests.filter(done=False)


class SongRequest:
    def __init__(self, uri: str):
        self.uri = uri
        self.data = redis.hgetall('request:' + uri)

    def _vote(self, direction: int, user_id: str) -> None:
        redis.set('vote:{}:{}'.format(self.uri, user_id), direction)

    def vote_up(self, user_id: str) -> None:
        redis.incr('votes:' + self.uri)
        self._vote(1, user_id)

    def vote_down(self, user_id: str) -> None:
        redis.decr('votes:' + self.uri)
        self._vote(-1, user_id)

    @property
    def user(self) -> str:
        return str(self.data['user'])

    @property
    def votes(self) -> int:
        try:
            return int(redis.get('votes:' + self.uri))
        except (ValueError, TypeError):
            return 0

    def get_user_vote(self, user_id: str) -> int:
        try:
            return int(redis.get('vote:{}:{}'.format(self.uri, user_id)))
        except (ValueError, TypeError):
            return 0

    def delete(self) -> None:
        redis.delete('request:' + self.uri)
        redis.delete('votes:' + self.uri)
        redis.srem('requests', self.uri)
        redis.srem('user:' + self.user, self.uri)

    def to_dict(self):
        return {'title': self.data['title'],
                'artist': self.data['artist'],
                'uri': self.uri,
                'votes': self.votes
                }

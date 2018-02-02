from flask_login import UserMixin
from passlib.handlers.sha2_crypt import sha256_crypt
from peewee import Model, OperationalError, CharField, BooleanField, ForeignKeyField, IntegerField

from config import DB


def db_init():
    DB.connect()
    try:
        DB.create_tables([User, SongRequest, Vote])
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


class SongRequest(BaseModel):
    title = CharField(null=True)
    artist = CharField(null=True)
    uri = CharField(unique=True)
    user = ForeignKeyField(User, related_name='requests')
    votes = IntegerField(default=0)
    done = BooleanField(default=False)

    def to_dict(self):
        d = self.__dict__['__data__']
        d.pop('user')
        return d


class Vote(BaseModel):
    user = ForeignKeyField(User, related_name='votes')
    song = ForeignKeyField(SongRequest, related_name='_votes')
    value = IntegerField(default=0)

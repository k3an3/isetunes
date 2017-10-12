from flask_login import UserMixin
from passlib.handlers.sha2_crypt import sha256_crypt
from peewee import Model, OperationalError, CharField, BooleanField

from config import DB


def db_init():
    DB.connect()
    try:
        DB.create_tables([User, ])
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

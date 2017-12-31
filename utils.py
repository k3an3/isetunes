from ldap3 import Server, Connection, ALL_ATTRIBUTES

import config
from models import User


def is_admin(r: str) -> bool:
    for g in [g.decode() for g in r['memberOf']]:
        if 'CN=Domain Admins,' in g:
            return True
    return False


def ldap_auth(username: str, password: str) -> User:
    s = Server(host=config.LDAP_HOST, port=config.LDAP_PORT, use_ssl=config.LDAP_SSL)
    with Connection(s, user=(username + '@iseage.org'), password=password) as c:
        u = None
        if c.bind():
            print("Successful bind for user " + username)
            c.search(search_base=config.LDAP_BASE_DN,
                     search_filter='({})'.format(config.LDAP_FILTER.format(username)),
                     attributes=ALL_ATTRIBUTES)
            r = c.response[0]['raw_attributes']
            u, created = User.get_or_create(username=username,
                                            defaults={'ldap': True,
                                                      'password': '',
                                                      'admin': is_admin(r)
                                                      })
            if created:
                print("Created new user from LDAP: " + username)
            else:
                u.admin = is_admin(r)
                u.save()
        else:
            print("Failed to bind with user " + config.LDAP_FILTER.format(username) + config.LDAP_BASE_DN)
        return u

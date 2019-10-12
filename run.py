#!/usr/bin/env python3

try:
    import eventlet

    eventlet.monkey_patch()
    print('Using eventlet')
    create_thread_func = lambda f: f
    start_thread_func = lambda f: eventlet.spawn(f)
except ImportError:
    try:
        import gevent
        import gevent.monkey

        gevent.monkey.patch_all()
        print('Using gevent')
        create_thread_func = lambda f: gevent.Greenlet(f)
        start_thread_func = lambda t: t.start()
    except ImportError:
        import threading

        print('Using threading')
        create_thread_func = lambda f: threading.Thread(target=f)
        start_thread_func = lambda t: t.start()

from isetunes.app import socketio, app
from config import DEBUG, SECRET_KEY
from isetunes.models import db_init

db_init()
module = globals().get('config', None)
app.config.update({key: value for key, value in module.__dict__.iteritems() if not (key.startswith('__') or key.startswith('_'))})
print(app.config['PLAYER'])
app.secret_key = SECRET_KEY
socketio.run(app, debug=DEBUG)

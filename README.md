Flask-SocketIO
==============

[![tests](https://code.miguelgrinberg.com/miguelgrinberg/flask-socketio/badges/workflows/tests.yml/badge.svg)](https://code.miguelgrinberg.com/miguelgrinberg/flask-socketio/actions)

Socket.IO integration for Flask applications.

Installation
------------

You can install this package as usual with pip:

    pip install flask-socketio

Example
-------

```py
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.event
def my_event(message):
    emit('my response', {'data': 'got it!'})

if __name__ == '__main__':
    socketio.run(app)
```

Resources
---------

- [Tutorial](http://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent)
- [git](https://code.miguelgrinberg.com/miguelgrinberg/flask-socketio)
- [Change Log](https://code.miguelgrinberg.com/miguelgrinberg/flask-socketio/src/branch/main/CHANGES.md)
- [Documentation](https://flask-socketio.readthedocs.io/)
- [PyPI](https://pypi.python.org/pypi/flask-socketio)
- [Contributor's guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Sponsor this project
--------------------

This project relies on contributions from its users. If you benefit from it please consider making a single or ongoing monetary contribution in one of the following platforms:

- [Github Sponsors](https://github.com/sponsors/miguelgrinberg)
- [Patreon](https://patreon.com/miguelgrinberg)
- [Buy me a Coffee](https://buymeacoffee.com/miguelgrinberg)
- [thanks.dev](https://thanks.dev/u/gh/miguelgrinberg)
- [PayPal](https://paypal.me/miguelgrinberg)

Thank you!

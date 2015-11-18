Flask-SocketIO
==============

[![Build Status](https://travis-ci.org/miguelgrinberg/Flask-SocketIO.png?branch=master)](https://travis-ci.org/miguelgrinberg/Flask-SocketIO)

Socket.IO integration for Flask applications.

Installation
------------

You can install this package as usual with pip:

    pip install flask-socketio

Example
-------

    from flask import Flask, render_template
    from flask_socketio import SocketIO, emit
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    socketio = SocketIO(app)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @socketio.on('my event')
    def test_message(message):
        emit('my response', {'data': 'got it!'})
    
    if __name__ == '__main__':
        socketio.run(app)

Resources
---------

- [Tutorial](http://blog.miguelgrinberg.com/post/easy-websockets-with-flask-and-gevent)
- [Documentation](http://pythonhosted.org/Flask-SocketIO)
- [PyPI](https://pypi.python.org/pypi/Flask-SocketIO)


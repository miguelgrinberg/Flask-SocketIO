from flask import Flask, render_template, session, request, jsonify
from flask_session import Session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, manage_session=False)


@app.route('/')
def index():
    session['value'] = ''
    return render_template('sessions.html')


@app.route('/session', methods=['GET', 'POST'])
def session_access():
    if request.method == 'GET':
        return jsonify({'session': session['value']})
    session['value'] = request.get_json().get('session')
    return '', 204


@socketio.on('get-session')
def get_session():
    emit('refresh-session', session['value'])


@socketio.on('set-session')
def set_session(value):
    session['value'] = value

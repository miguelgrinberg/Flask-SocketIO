# #!/usr/bin/env python
# from threading import Lock
# from flask import Flask, render_template, session, request
# from flask_socketio import SocketIO, emit, join_room, leave_room, \
#     close_room, rooms, disconnect


# # Set this variable to "threading", "eventlet" or "gevent" to test the
# # different async modes, or leave it set to None for the application to choose
# # the best option based on installed packages.
# async_mode = None

# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
# socketio = SocketIO(app, async_mode=async_mode)
# thread = None
# thread_lock = Lock()


# def background_thread():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         socketio.sleep(10)
#         count += 1
#         socketio.emit('my_response',
#                       {'data': 'Server generated event', 'count': count},
#                       namespace='/test')


# @app.route('/')
# def index():
#     return render_template('index.html', async_mode=socketio.async_mode)

# @app.route('/json-example', methods=['POST']) #GET requests will be blocked
# def json_example():
#     print("############################################")
#     req_data = request.get_json()

#     language = req_data['language']
#     framework = req_data['framework']
#     python_version = req_data['version_info']['python'] #two keys are needed because of the nested object
#     example = req_data['examples'][0] #an index is needed because of the array
#     boolean_test = req_data['boolean_test']


#     return '''
#            The language value is: {}
#            The framework value is: {}
#            The Python version is: {}
#            The item at index 0 in the example list is: {}
#            The boolean value is: {}'''.format(language, framework, python_version, example, boolean_test)

    
# @app.route('/json-ttn', methods=['POST']) #GET requests will be blocked
# def json_ttn():
#     print("############################################")
#     req_data = request.get_json()
#     _login = req_data['payload_fields']['SensorId']
#     _password = req_data['payload_fields']['Value']
#     _value = req_data['payload_fields']['SensorPassword']


#     socketio.emit('my_response',
#                 {'data': 'Server generated event', 'count': 4242},
#                 namespace='/test')    
#     # import urllib.request
#     # import json  
#     # print("############################################")
#     # _body =  { "SensorId": _login, "Value":_value, "SensorPassword":_password}
#     # _myurl = "https://lorastore20181206101456.azurewebsites.net/api/Measurements"
#     # _req = urllib.request.Request(_myurl)
#     # _req.add_header('Content-Type', 'application/json; charset=utf-8')
#     # jsondata = json.dumps(_body)
#     # jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
#     # _req.add_header('Content-Length', len(jsondataasbytes))
#     # print (jsondataasbytes)
#     # _response = urllib.request.urlopen(_req, jsondataasbytes)
#     # # print(_response.msg)
#     # print(_response.status)
#     # # print(_response.read() )
#     # print("END!!!!!")

#     return '''
#            SensorId: {}
#            Value: {}
#            SensorPassword: {}'''.format(_login,_value,_password)

#     # language = req_data['app_id']
#     # framework = req_data['payload_fields']
#     # python_version = req_data['dev_id']['python'] #two keys are needed because of the nested object
#     # example = req_data['dev_id'][0] #an index is needed because of the array
#     # boolean_test = req_data['dev_id']

#     # return '''
#     #        The language value is: {}
#     #        The framework value is: {}
#     #        The Python version is: {}
#     #        The item at index 0 in the example list is: {}
#     #        The boolean value is: {}'''.format(language, framework, python_version, example, boolean_test)

    
# @app.route('/request', methods=['GET', 'POST'])
# def req():
#     import urllib.request
#     from random import randint
#     import json    
#     import time
#     _login = 45 # Your SensorId
#     _password = "45"
#     print("############################################")
#     temp = 10 + (randint(0, 200)/10)
#     body =  { "SensorId": _login, "Value":temp, "SensorPassword":_password}
#     myurl = "https://lorastore20181206101456.azurewebsites.net/api/Measurements"
#     req = urllib.request.Request(myurl)
#     req.add_header('Content-Type', 'application/json; charset=utf-8')
#     jsondata = json.dumps(body)
#     jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
#     req.add_header('Content-Length', len(jsondataasbytes))
#     print (jsondataasbytes)
#     response = urllib.request.urlopen(req, jsondataasbytes)
#     print(response.msg)
#     print(response.status)
#     print(response.read() )
#     print("END!!!!!")
#     return render_template('request.html', async_mode=socketio.async_mode)


# @socketio.on('my_event', namespace='/test')
# def test_message(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': message['data'], 'count': session['receive_count']})


# @socketio.on('my_broadcast_event', namespace='/test')
# def test_broadcast_message(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': message['data'], 'count': session['receive_count']},
#          broadcast=True)


# @socketio.on('join', namespace='/test')
# def join(message):
#     join_room(message['room'])
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': 'In rooms: ' + ', '.join(rooms()),
#           'count': session['receive_count']})


# @socketio.on('leave', namespace='/test')
# def leave(message):
#     leave_room(message['room'])
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': 'In rooms: ' + ', '.join(rooms()),
#           'count': session['receive_count']})


# @socketio.on('close_room', namespace='/test')
# def close(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
#                          'count': session['receive_count']},
#          room=message['room'])
#     close_room(message['room'])


# @socketio.on('my_room_event', namespace='/test')
# def send_room_message(message):
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': message['data'], 'count': session['receive_count']},
#          room=message['room'])


# @socketio.on('disconnect_request', namespace='/test')
# def disconnect_request():
#     session['receive_count'] = session.get('receive_count', 0) + 1
#     emit('my_response',
#          {'data': 'Disconnected!', 'count': session['receive_count']})
#     disconnect()


# @socketio.on('my_ping', namespace='/test')
# def ping_pong():
#     emit('my_pong')


# @socketio.on('connect', namespace='/test')
# def test_connect():
#     global thread
#     with thread_lock:
#         if thread is None:
#             thread = socketio.start_background_task(background_thread)
#     emit('my_response', {'data': 'Connected', 'count': 0})


# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print('Client disconnected', request.sid)


# if __name__ == '__main__':
#     socketio.run(app, debug=True)

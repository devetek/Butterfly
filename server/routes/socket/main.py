from flask import request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect


def routes(socketio):
    @socketio.on('my_event', namespace='/test')
    def test_message(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']})

    @socketio.on('my_broadcast_event', namespace='/test')
    def test_broadcast_message(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             broadcast=True)

    @socketio.on('join', namespace='/test')
    def join(message):
        join_room(message['room'])
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session['receive_count']})

    @socketio.on('leave', namespace='/test')
    def leave(message):
        leave_room(message['room'])
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'In rooms: ' + ', '.join(rooms()),
              'count': session['receive_count']})

    @socketio.on('close_room', namespace='/test')
    def close(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response', {'data': 'Room ' + message['room'] + ' is closing.',
                             'count': session['receive_count']},
             room=message['room'])
        close_room(message['room'])

    @socketio.on('my_room_event', namespace='/test')
    def send_room_message(message):
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': message['data'], 'count': session['receive_count']},
             room=message['room'])

    @socketio.on('disconnect_request', namespace='/test')
    def disconnect_request():
        session['receive_count'] = session.get('receive_count', 0) + 1
        emit('my_response',
             {'data': 'Disconnected!', 'count': session['receive_count']})
        disconnect()

    @socketio.on('my_ping', namespace='/test')
    def ping_pong():
        emit('my_pong')

    @socketio.on_error()
    def error_handler_chat(e):
        pass

    @socketio.on('connect', namespace='/test')
    def test_connect():
        emit('my_response', {'data': 'Connected', 'count': 0})
        # global thread
        # with thread_lock:
        #     if thread is None:
        #         thread = socketio.start_background_task(background_thread)
        # emit('my_response', {'data': 'Connected', 'count': 0})

    @socketio.on('disconnect', namespace='/test')
    def test_disconnect():
        print('Client disconnected', request.sid)

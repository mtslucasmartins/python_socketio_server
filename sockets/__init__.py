from flask_socketio import SocketIO, emit, disconnect

socket_io = SocketIO()


class Socket:
    def __init__(self, sid):
        self.sid = sid
        self.connected = True

    # Emits data to a socket's unique room
    def emit(self, event, data):
        emit(event, data, room=self.sid)

    def disconnect(self):
        disconnect(self.sid)

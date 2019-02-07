import base64
import json
import time
import uuid
from settings import DATABASE_URI, PORT
from database import db as database
from database.models import User, Session
from sockets.sockets import *
from flask import abort, Flask, g as request_context, request, Response

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

database.init_app(app)
socket_io.init_app(app)


@app.errorhandler(401)
def error_401(error):
    return Response({'status': 'error', 'message': 'Full authentication is required to access this resource!'}, 401)


@app.before_request
def request_headers_validation():
    header_authorization = request.headers.get('Authorization')
    header_authorization = '' if header_authorization is None else header_authorization

    if header_authorization.startswith('Bearer '):
        header_authorization = header_authorization.replace('Bearer ', '')
        request_context.user = Session.query.filter(Session.token == header_authorization).limit(1)[0].user
    elif header_authorization.startswith('Basic '):
        header_authorization = header_authorization.replace('Basic ', '')
        (username, password) = base64.b64decode(header_authorization.encode()).decode().split(':')
        request_context.user = User.query.filter(User.email == username and User.password == password).limit(1)[0]
    else:
        abort(401)


@app.route('/services/users/info')
def users_info():
    return json.dumps(request_context.user.as_json())


@app.route('/services/sockets/info')
def sockets_info():
    print([s for s in sockets])
    return json.dumps([s for s in sockets])


@app.route("/services/users/<user_id>")
def get_users_by_id(user_id):
    start = time.time()

    users = User.query.filter(User.id == user_id).order_by(User.email.desc())
    dumps = json.dumps([user.as_json() for user in users])

    print('get_users_by_id took {} ms'.format((time.time() - start)))
    return dumps


@app.route("/services/auth/ticket")
def generate_websocket_ticket():
    user_id = str(round(request_context.user.id))
    user_ticket = str(uuid.uuid4())

    authorized_tickets[user_ticket] = user_id

    response = json.dumps({'status': 'success', 'ticket': user_ticket})

    return response


@app.route("/services/messages/<message_id>/received/<contact_id>")
def update_message_set_received(message_id, contact_id):
    message_service.update_message_set_received(message_id, contact_id, request_context.user)
    return json.dumps({'status': 'success'})


@app.route("/services/messages/<message_id>/seen/<contact_id>")
def update_message_set_seen(message_id, contact_id):
    message_service.update_message_set_seen(message_id, contact_id, request_context.user)
    return json.dumps({'status': 'success'})


if __name__ == "__main__":
    socket_io.run(app, host='0.0.0.0', port=PORT, debug=True)

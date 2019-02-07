from flask import request
from flask_socketio import disconnect
from database.models import Message, Contact
from services import message_service
from sockets import Socket, socket_io
from datetime import datetime

authorized_tickets = {}
sockets = {}

NAMESPACE = '/messages'


@socket_io.on('connect')
def on_something():
    print('User connected on something')


@socket_io.on('connect', namespace=NAMESPACE)
def on_connect():
    """Validates user connection.

    Receives a User ID and Ticket and validates with authorized tickets
    disconnects if ticket isn't valid.
    """
    print('User connected on /messages')

    # request arguments for ticket validation.
    user_id = str(request.args.get('user_id'))
    user_ticket = str(request.args.get('ticket'))

    is_valid = False

    # checks whether the tickets is valid for this user or not.
    if user_ticket in authorized_tickets:
        is_valid = authorized_tickets[user_ticket] == user_id

    # if the ticket is valid saves the session, else disconnects the user.
    sockets[user_id] = Socket(request.sid) if is_valid else disconnect()


@socket_io.on('disconnect', namespace=NAMESPACE)
def on_disconnect():
    """Removes the session from memory when a user disconnects."""
    user_id = str(request.args.get('user_id'))

    if user_id in sockets:
        del sockets[user_id]


@socket_io.on('message::created', namespace=NAMESPACE)
def on_message_created(data):
    print('on_message_created')
    user_id = str(request.args.get('user_id'))

    # datetime.fromtimestamp(data['createdAt'] / 1e3)
    created_at = datetime.strptime(data['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')

    # jsdate -> %Y-%m-%dT%H:%M:%SZ

    message = Message(content=data['content'],
                      contact=Contact.query.filter(Contact.fk_users_id == user_id).first(),
                      chat=data['chat'],
                      type=data['type'] if 'type' in data else 0,
                      status=1,
                      updated_at=datetime.now(),
                      created_at=created_at)

    message_service.create_message(message)

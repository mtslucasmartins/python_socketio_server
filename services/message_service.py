from database import db
from database.models import ChatContacts, Message, MessageContact, Contact
from sockets import sockets


def create_message(message):
    """Inserts a message to database, and sends it to the contacts related to the conversation."""
    # Inserts the message to the database, and flushes it in order to get the generated id.
    db.session.add(message)
    db.session.flush()
    db.session.commit()

    # Search for contacts related to the conversation.
    chat_contacts = ChatContacts.query.filter(ChatContacts.fk_chats_id == message.fk_chats_id)

    # Iterates the conversation contacts and inserts a row in message_contacts.
    for chat_contact in chat_contacts:
        user_id = '{}'.format(chat_contact.contact.fk_users_id)
        message_contact = MessageContact(message.server_id, chat_contact.contact.id)

        db.session.add(message_contact)
        db.session.commit()

        # sends the message to the user, if connected.
        if user_id in sockets.sockets:
            try:
                sockets.sockets[user_id].emit('message::created', message.as_json())
            except Exception as ex:
                print(ex)


def update_message_set_received(message_id, contact_id, user=None) -> None:
    """Sets a Message as Received by Message Id and Contact Id."""
    user = user if user is not None else Contact.query.filter(Contact.id == contact_id).first().user

    message = Message.query.filter(Message.server_id == message_id).first()

    db.session.query() \
        .filter(MessageContact.fk_messages_id == message_id
                and MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True})
    db.session.commit()

    # if the message is not yet received by any user,
    # updates the reference and emits a message to the sender.
    if message.status < 2:
        message.status = 2

        db.session.query() \
            .filter(Message.server_id == message_id) \
            .update({'status': message.status})
        db.session.commit()

        # sends the message to the user, if connected.
        if user.id in sockets.sockets:
            try:
                sockets.sockets[user.id].emit('message::updated', message.as_json())
            except Exception as ex:
                print(ex)


def update_message_set_seen(message_id, contact_id, user=None) -> None:
    """Sets a Message as Read by Message Id and Contact Id."""
    user = user if user is not None else Contact.query.filter(Contact.id == contact_id).first().user

    message = Message.query.filter(Message.server_id == message_id).first()

    db.session.query() \
        .filter(MessageContact.fk_messages_id == message_id
                and MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True, 'is_seen': True})
    db.session.commit()

    # if the message is not yet viewed,
    # updates the reference and emits a message to the sender.
    if message.status < 3:
        message.status = 3

        db.session.query() \
            .filter(Message.server_id == message_id) \
            .update({'status': message.status})
        db.session.commit()

        # sends the message to the user, if connected.
        if user.id in sockets.sockets:
            try:
                sockets.sockets[user.id].emit('message::updated', message.as_json())
            except Exception as ex:
                print(ex)

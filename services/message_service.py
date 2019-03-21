from database import db
import database.models as models

from sockets import sockets

import json

import notifications

def create_message(message):
    """Inserts a message to database, and sends it to the contacts related to the conversation."""

    # Inserts the message to the database, and flushes it in order to get the generated id.
    db.session.add(message)
    db.session.flush()
    db.session.commit()
    
    # gets the reference by id from database.
    message = models.Message.query.filter(models.Message.server_id == message.server_id).first()
    
    # Search for contacts related to the conversation.
    chat_contacts = models.ChatContacts.query.filter(models.ChatContacts.fk_chats_id == message.fk_chats_id)

    # Iterates the conversation contacts and inserts a row in message_contacts.
    for chat_contact in chat_contacts:
        if chat_contact.contact.fk_users_id is not None:
            user_id = str(round(chat_contact.contact.fk_users_id))
            message_contact = models.MessageContact(message.server_id, chat_contact.contact.id)

            db.session.add(message_contact)
            db.session.commit()

            # sends the message to the user, if connected.
            if user_id in sockets.sockets:
                try:
                    sockets.sockets[user_id].emit('message::created', message.as_json())

                    # Web Push Notifications
                    user_endpoints = models.UserEndpoint.query.filter(models.UserEndpoint.fk_users_id == user_id)
                    print('Iteating over user endpoints...')
                    for user_endpoint in user_endpoints:
                        data = notifications.WebPushNotificationData()
                        action = notifications.WebPushNotificationAction("teste", "Go to the site")

                        notification = notifications.WebPushNotification(message.chat.subject, "Novas Mensagens", "assets/icons/icon-512x512.png", data)
                        notification.append_action(action)
                        
                        print('Sending Notification.')
                        notifications.send_webpush_notification(notification, json.loads(user_endpoint.endpoint))

                except Exception as ex:
                    print("""Exception at message_service.py 'create_message'""")
                    print(ex)


def update_message_set_received(message_id, contact_id) -> None:
    """Sets a Message as Received by Message Id and Contact Id."""
    message = models.Message.query.filter(models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(models.Contact.id == contact_id).first()

    db.session.query(models.MessageContact) \
        .filter(models.MessageContact.fk_messages_id == message_id,
                models.MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True})
    db.session.commit()

    set_received_before_id(message_id, contact_id)

    # if the message is not yet received by any user,
    # updates the reference and emits a message to the sender.
    if contact.id != message.contact.id:
        if message.contact.user is not None:
            user_id = str(round(message.contact.user.id))
            if message.status < 2:
                message.status = 2
                db.session.query(models.Message) \
                    .filter(models.Message.server_id == message_id) \
                    .update({'status': message.status})
                db.session.commit()

                # sends the message to the user, if connected.
                if user_id in sockets.sockets:
                    try:
                        sockets.sockets[user_id].emit('message::updated', message.as_json())
                    except Exception as ex:
                        print("""Exception at message_service.py 'update_message_set_received'""")
                        print(ex)


def update_message_set_seen(message_id, contact_id) -> None:
    """Sets a Message as Read by Message Id and Contact Id."""
    message = models.Message.query.filter(models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(models.Contact.id == contact_id).first()

    db.session.query(models.MessageContact) \
        .filter(models.MessageContact.fk_messages_id == message_id,
                models.MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True, 'is_seen': True})
    db.session.commit()

    set_seen_before_id(message_id, contact_id)

    # if the message is not yet viewed,
    # updates the reference and emits a message to the sender.
    if contact.id != message.contact.id:
        if message.contact.user is not None:
            user_id = str(round(message.contact.user.id))
            if message.status < 3:
                message.status = 3
                db.session.query(models.Message) \
                    .filter(models.Message.server_id == message_id) \
                    .update({'status': message.status})
                db.session.commit()

                # sends the message to the user, if connected.
                if user_id in sockets.sockets:
                    try:
                        sockets.sockets[user_id].emit('message::updated', message.as_json())
                    except Exception as ex:
                        print("""Exception at message_service.py 'update_message_set_seen'""")
                        print(ex)


def set_received_before_id(message_id, contact_id) -> None:
    """Sets a Message as Read by Message Id and Contact Id."""
    message = models.Message.query.filter(models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(models.Contact.id == contact_id).first()

    db.session.query(models.MessageContact) \
        .filter(models.MessageContact.fk_messages_id < message_id,
                models.MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True})
    db.session.commit()

    if contact.id != message.contact.id:
        message.status = 2
        db.session.query(models.Message) \
            .filter(models.Message.server_id < message_id) \
            .filter(models.Message.status < message.status) \
            .update({'status': message.status})
        db.session.commit()


def set_seen_before_id(message_id, contact_id) -> None:
    """Sets a Message as Received by Message Id and Contact Id."""
    message = models.Message.query.filter(models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(models.Contact.id == contact_id).first()

    db.session.query(models.MessageContact) \
        .filter(models.MessageContact.fk_messages_id < message_id,
                models.MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True, 'is_seen': True})
    db.session.commit()

    if contact.id != message.contact.id:
        message.status = 3
        db.session.query(models.Message) \
            .filter(models.Message.server_id < message_id) \
            .filter(models.Message.status < message.status) \
            .update({'status': message.status})
        db.session.commit()




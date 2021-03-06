from sqlalchemy import or_, and_, func

import database.models as models
import notifications as notifications

from database import db
from sockets import sockets

import json


def count_pending_messages(chat_id, contact_id):
    try:
        count = db.session.execute(
            """
            select count(message.server_id) from messages message
                inner join messages_contacts messageContact
                on (
                    message.server_id = messageContact.fk_messages_id
                    and
                    messageContact.fk_contacts_id = :contactId
                )
            where message.fk_chats_id = :chatId
            and message.fk_contacts_id != :contactId
            and (
                messageContact.is_received = false
                or
                messageContact.is_seen = false
            ) """, {
                'chatId': chat_id,
                'contactId': contact_id
            }).scalar()
    except:
        count = 1

    return count


def create_message(message, user_id):
    """Inserts a message to database, and sends it to the contacts related to the conversation."""
    message.make_external_id()

    # Inserts the message to the database, and flushes it in order to get the generated id.
    db.session.add(message)
    db.session.flush()
    db.session.commit()

    # gets the reference by id from database.
    message = models.Message.query.filter(
        models.Message.server_id == message.server_id).first()

    # Search for contacts related to the conversation.
    chat_contacts = models.ChatContacts.query.filter(
        models.ChatContacts.fk_chats_id == message.fk_chats_id)

    # Iterates the conversation contacts and inserts a row in message_contacts.
    for chat_contact in chat_contacts:
        contact_id = chat_contact.contact.id
        if chat_contact.contact.fk_users_id is not None:

            if chat_contact.closed_date is not None:
                db.session.query(models.ChatContacts) \
                  .filter(models.ChatContacts.fk_chats_id == message.fk_chats_id) \
                    .update({'closed_date': None})
                db.session.commit()

            contact_user_id = str(round(chat_contact.contact.fk_users_id))
            message_contact = models.MessageContact(message.server_id,
                                                    chat_contact.contact.id)

            db.session.add(message_contact)
            db.session.commit()

            # sends the message to the user, if connected.
            if contact_user_id in sockets.sockets:
                try:
                    sockets.sockets[contact_user_id].emit(
                        'message::created', message.as_json())
                except Exception as ex:
                    print(
                        """Exception at message_service.py 'create_message'""")
                    print(ex)

            # Web Push Notifications
            if user_id != contact_user_id:

                try:
                    print('>>> Counting pending messages...')
                    count = count_pending_messages(message.fk_chats_id,
                                                   contact_id)

                    print('>>> Getting User Endpoints for Push...')
                    user_endpoints = models.UserEndpoint.query.filter(
                        models.UserEndpoint.fk_users_id ==
                        chat_contact.contact.fk_users_id)
                    for user_endpoint in user_endpoints:
                        notification_data = notifications.WebPushNotificationData(
                        )
                        notification_action = notifications.WebPushNotificationAction(
                            "teste", "Go to the site")

                        notification_title = message.chat.subject
                        notification_body = "Novas Mensagens"
                        notification_icon = "assets/icons/icon-512x512.png"
                        notification_tag = str(message.chat.id)

                        if count > 1:
                            notification_body = "Você possui {} novas mensagens!".format(
                                count)
                        else:
                            notification_body = "Você possui uma nova mensagem!"

                        notification = notifications.WebPushNotification(
                            notification_title, notification_body,
                            notification_icon, notification_tag,
                            notification_data)
                        notification.append_action(notification_action)

                        notification.push(json.loads(user_endpoint.endpoint))
                except Exception as e:
                    print(e)


def update_message_set_received(message_id, contact_id) -> None:
    """Sets a Message as Received by Message Id and Contact Id."""
    message = models.Message.query.filter(
        models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(
        models.Contact.id == contact_id).first()

    db.session.query(models.MessageContact) \
        .filter(models.MessageContact.fk_messages_id == message_id,
                models.MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True})
    db.session.commit()

    # try:
    #     set_received_before_id(message_id, contact_id)
    # except Exception as e:
    #     print(e)

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
                        sockets.sockets[user_id].emit('message::updated',
                                                      message.as_json())
                    except Exception as ex:
                        print(
                            """Exception at message_service.py 'update_message_set_received'"""
                        )
                        print(ex)


def update_message_set_seen(message_id, contact_id) -> None:
    """Sets a Message as Read by Message Id and Contact Id."""
    message = models.Message.query.filter(
        models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(
        models.Contact.id == contact_id).first()

    db.session.query(models.MessageContact) \
        .filter(models.MessageContact.fk_messages_id == message_id,
                models.MessageContact.fk_contacts_id == contact_id) \
        .update({'is_received': True, 'is_seen': True})
    db.session.commit()

    # try:
    #     set_seen_before_id(message_id, contact_id)
    # except Exception as e:
    #     print(e)

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
                        sockets.sockets[user_id].emit('message::updated',
                                                      message.as_json())
                    except Exception as ex:
                        print(
                            """Exception at message_service.py 'update_message_set_seen'"""
                        )
                        print(ex)


def set_received_before_id(message_id, contact_id) -> None:
    """Sets a Message as Read by Message Id and Contact Id."""
    message = models.Message.query.filter(
        models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(
        models.Contact.id == contact_id).first()

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
    message = models.Message.query.filter(
        models.Message.server_id == message_id).first()
    contact = models.Contact.query.filter(
        models.Contact.id == contact_id).first()

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


class MessageService:
    """ Service for Messages """

    def save(self, message):
        """Saves a new message on database."""
        print('Saving new message...')

    def received(self, message):
        """Updates message on database mark as received."""
        print('Marking message as received by ...')

    def read(self, message):
        """Updates message on database mark as seen."""
        print('Marking message as seen by ...')

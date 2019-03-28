from database import db

import time
import datetime
import json


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    email = db.Column(db.String(), unique=True)
    password = db.Column(db.String(), unique=False)

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "password": self.password,
        }
        

class UserEndpoint(db.Model):
    __tablename__ = 'users_push_endpoints'

    fk_users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, primary_key=True)
    user = db.relationship('User', foreign_keys='UserEndpoint.fk_users_id')

    endpoint = db.Column(db.String(), nullable=False, primary_key=True)

    def __init__(self, fk_users_id=None, endpoint=None):
        self.fk_users_id = fk_users_id
        self.endpoint = endpoint

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        return {
            "user": self.user.as_json(),
            "endpoint": self.content
        }
        

class Session(db.Model):
    __tablename__ = 'authorized_tokens'

    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    token = db.Column(db.String(), unique=True)
    created_at = db.Column(db.Date(), unique=False)
    updated_at = db.Column(db.Date(), unique=False)

    fk_users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', foreign_keys='Session.fk_users_id')

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        return {
            "id": str(self.id),
            "token": self.token,
            "created_at": time.mktime(self.created_at.timetuple()) * 1e3,
            "updated_at": time.mktime(self.updated_at.timetuple()) * 1e3,
            "user": self.user.as_json()
        }


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    description = db.Column(db.String(), unique=True)
    short_description = db.Column(db.String(), unique=False)

    fk_users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', foreign_keys='Contact.fk_users_id')

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        json = {}

        if self.id is not None:
            json['id'] = str(round(self.id))

        json['description'] = self.description
        json['shortDescription'] = self.short_description

        if self.user is not None:
            json['user'] = self.user.as_json()

        
        return json


class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    subject = db.Column(db.String(), unique=False)
    created_at = db.Column(db.Date(), unique=False)
    updated_at = db.Column(db.Date(), unique=False)

    fk_contacts_from = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    contact_from = db.relationship('Contact', foreign_keys='Chat.fk_contacts_from')

    fk_contacts_to = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    contact_to = db.relationship('Contact', foreign_keys='Chat.fk_contacts_to')

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        return {
            "id": str(round(self.id)),
            "subject": self.subject,
            "contactFrom": self.contact_from.as_json(),
            "contactTo": self.contact_to.as_json(),
        }


class ChatContacts(db.Model):
    __tablename__ = 'chat_contacts'

    fk_chats_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False, primary_key=True)
    chat = db.relationship('Chat', foreign_keys='ChatContacts.fk_chats_id')

    fk_contacts_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False, primary_key=True)
    contact = db.relationship('Contact', foreign_keys='ChatContacts.fk_contacts_id')

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        return {
            "chat": self.chat.as_json(),
            "contact": self.contact.as_json(),
        }


class Message(db.Model):
    __tablename__ = 'messages'

    server_id = db.Column(db.Integer, db.Sequence('messages_sequence_id'), unique=True, nullable=False,
                          primary_key=True)
    device_id = db.Column(db.Integer, unique=False, nullable=True)

    content = db.Column(db.String(), unique=False, nullable=True)
    status = db.Column(db.Integer, unique=False, nullable=True)
    type = db.Column(db.Integer, unique=False, nullable=True)

    created_at = db.Column(db.Date(), unique=False, nullable=True)
    updated_at = db.Column(db.Date(), unique=False, nullable=True)

    fk_contacts_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    contact = db.relationship('Contact', foreign_keys='Message.fk_contacts_id')

    fk_chats_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    chat = db.relationship('Chat', foreign_keys='Message.fk_chats_id')

    def __init__(self, **kwargs):
        self.server_id = kwargs['server_id'] if 'server_id' in kwargs else None
        self.device_id = kwargs['device_id'] if 'device_id' in kwargs else None

        self.content = kwargs['content'] if 'content' in kwargs else None

        self.fk_contacts_id = kwargs['fk_contacts_id'] if 'fk_contacts_id' in kwargs else None
        self.fk_chats_id = kwargs['fk_chats_id'] if 'fk_chats_id' in kwargs else None

        self.status = kwargs['status'] if 'status' in kwargs else 0
        self.type = kwargs['type'] if 'type' in kwargs else 0

        self.created_at = kwargs['created_at'] if 'created_at' in kwargs else datetime.datetime.fromtimestamp(
            kwargs['created_at'] / 1e3)
        self.updated_at = kwargs['updated_at'] if 'updated_at' in kwargs else datetime.datetime.fromtimestamp(
            kwargs['updated_at'] / 1e3)

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def make_external_id(self):
        chat_id = self.fk_chats_id
        contact_id = self.fk_contacts_id
        created_at = self.created_at

        print("""
            chat_id =     {}
            contact_id =  {}
            created_at =  {}
        """.format(chat_id, contact_id, created_at))


    def as_json(self):
        json = {}

        created_at = time.mktime(self.created_at.timetuple())*1e3 + self.created_at.microsecond/1e3
        updated_at = time.mktime(self.updated_at.timetuple())*1e3 + self.created_at.microsecond/1e3

        if self.server_id is not None:
            json['serverId'] = str(round(self.server_id)) 
        
        if self.device_id is not None:
            json['deviceId'] = str(round(self.device_id)) 
        
        json['content'] = self.content

        if self.contact is not None:
            json['contact'] = self.contact.as_json()

        if self.chat is not None:
            json['chat'] = self.chat.as_json()

        json['createdAt'] = created_at
        json['updatedAt'] = updated_at
    
        json['status'] = self.status
        json['type'] = self.type

        return json

class MessageContact(db.Model):
    __tablename__ = 'messages_contacts'

    fk_messages_id = db.Column(db.Integer, db.ForeignKey('messages.server_id'), nullable=False, primary_key=True)
    message = db.relationship('Message', foreign_keys='MessageContact.fk_messages_id')

    fk_contacts_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False, primary_key=True)
    contact = db.relationship('Contact', foreign_keys='MessageContact.fk_contacts_id')

    is_received = db.Column(db.Boolean, unique=False, nullable=True, default=False)
    is_seen = db.Column(db.Boolean, unique=False, nullable=True, default=False)

    def __init__(self, fk_messages_id=None, fk_contacts_id=None, is_received=False, is_seen=False):
        self.fk_messages_id = fk_messages_id
        self.fk_contacts_id = fk_contacts_id
        self.is_received = is_received
        self.is_seen = is_seen

    def __repr__(self):
        return str(json.dumps(self.as_json()))

    def as_json(self):
        return {
            "serverId": str(self.server_id),
            "content": self.content,
            "status": self.status,
            "type": self.type,
            "contact": self.contact.as_json(),
            "chat": self.chat.as_json()
        }

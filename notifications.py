# from pywebpush import webpush, WebPushException

import pywebpush as wp


from datetime import datetime, timedelta

import json
import pytz
import time

expiration_time = datetime.now() + timedelta(hours=23)
expiration_time = time.mktime(expiration_time.timetuple()) * 1e3 + expiration_time.microsecond / 1e3

vapid = {
    "claims": {
        "sub": "mailto:lucas@ottimizza.com.br",
        "exp": datetime.now() + timedelta(hours=23)
    },
    "public_key": "BLSKBIHrsFCeLUO3FwI95mfSubQiZlno-CTZPDBBoTH6P4CQ-SnEZtlBNM-TWRlk-u3Q36JdjLLk69WYNWJ2rOw",
    "private_key": "d-FafnJ0zkCN3zH0Vvz9arsvCX15oMk8WmyJyBjWFM0"
}

timezone = pytz.timezone('America/Sao_Paulo')

class WebPushNotificationData:
    """Model for Push API Notification Data."""
    def __init__(self, date_of_arrival = datetime.now(), primary_key = 1):
        self.date_of_arrival = date_of_arrival
        self.primary_key = primary_key

    def json(self):
        return {
            "dateOfArrival": self.date_of_arrival.astimezone(timezone).isoformat(),
            "primaryKey": self.primary_key
        }

class WebPushNotificationAction:
    """Model for Push API Notification Actions."""
    def __init__(self, action = "", title = ""):
        self.action = action
        self.title = title

    def json(self):
        return {
            "action": self.action,
            "title": self.title
        }

class WebPushNotification:
    """"""
    def __init__(self, title, body, icon, tag, data, vibrate = [100, 50, 100]):
        self.title = title
        self.body = body
        self.icon = icon
        self.tag = tag
        self.vibrate = vibrate

        self.data = data
        self.actions = []

    def append_action(self, action):
        self.actions.append(action.json())

    def push(self, subscription_info):
        try:
            data = str(self)
            vapid_private_key = vapid.get("private_key")
            vapid_claims = vapid.get("claims")

            print(">>> Pushing Notification...\n")
            print("      endpoint          ...:  {}".format(json.dumps(subscription_info)))
            print("      data              ...:  {}".format(data))
            print("      vapid_private_key ...:  {}".format(vapid_private_key))
            print("      vapid_claims      ...:  {}".format(json.dumps(vapid.get("claims"))))
            print("")

            wp.webpush(subscription_info=subscription_info, data=data, vapid_private_key=vapid_private_key, vapid_claims=vapid_claims)
        except wp.WebPushException as ex:
            print("I'm sorry, Dave, but I can't do that: {}", repr(ex))
            # Mozilla returns additional information in the body of the response.
            if ex.response and ex.response.json():
                extra = ex.response.json()
                print("Remote service replied with a {}:{}, {}",
                    extra.code,
                    extra.errno,
                    extra.message
            )
        except Exception as e:
            print(e)

    def json(self):
        return {
            "title": self.title,
            "body": self.body,
            "icon": self.icon,
            "tag": self.tag,
            "vibrate": self.vibrate,
            "data": self.data.json(),
            "actions": self.actions
        }
    
    def __repr__(self):
        return json.dumps({'notification': self.json()})

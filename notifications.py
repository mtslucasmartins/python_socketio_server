from pywebpush import webpush, WebPushException

from datetime import datetime
from pytz import timezone

import json

# WARNING
import sys
sys.setrecursionlimit(1500)


public_key = "BLSKBIHrsFCeLUO3FwI95mfSubQiZlno-CTZPDBBoTH6P4CQ-SnEZtlBNM-TWRlk-u3Q36JdjLLk69WYNWJ2rOw"
private_key = "d-FafnJ0zkCN3zH0Vvz9arsvCX15oMk8WmyJyBjWFM0"


timezone = timezone('America/Sao_Paulo')

class WebPushNotificationData:
    """"""
    def __init__(self, date_of_arrival = datetime.now(), primary_key = 1):
        self.date_of_arrival = date_of_arrival
        self.primary_key = primary_key

    def json(self):
        return {
            "dateOfArrival": self.date_of_arrival.astimezone(timezone).isoformat(),
            "primaryKey": self.primary_key
        }

class WebPushNotificationAction:
    """"""
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
    def __init__(self, title, body, icon, data, vibrate = [100, 50, 100]):
        self.title = title
        self.body = body
        self.icon = icon
        self.vibrate = vibrate

        self.data = data
        self.actions = []

    def append_action(self, action):
        self.actions.append(action.json())

    def json(self):
        return {
            "title": self.title,
            "body": self.body,
            "icon": self.icon,
            "vibrate": self.vibrate,
            "data": self.data.json(),
            "actions": self.actions
        }


def send_webpush_notification(notification, endpoint):
    try:
        print('Building...')
        body = json.dumps({
            "notification": {
                "title": notification.title,
                "icon": notification.icon,
                "body": notification.body,
                "vibrate": notification.vibrate,
                "data": {
                    "dateOfArrival": notification.data.date_of_arrival.astimezone(timezone).isoformat(),
                    "primaryKey": notification.data.primary_key
                },
                "actions": notification.actions
            }
        })

        print('Sending...')

        webpush(
            subscription_info=endpoint,
            data=body,
            vapid_private_key=private_key,  # "mp5xYHWtRTyCA63nZMvmJ_qmYO6A1klSotcoppSx-MI",
            vapid_claims={"sub": "mailto:lucas@ottimizza.com.br"}
        )
    except WebPushException as ex:
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

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


class WebPushNotification:

    @staticmethod
    def send_webpush_notification(title, body, endpoint):
        try:
            print('Building...')
            body = json.dumps({
                "notification": {
                    "title": title,
                    "icon": "assets/icons/icon-512x512.png",
                    "body": body,
                    "vibrate": [100, 50, 100],
                    "data": {
                        "dateOfArrival": datetime.now().astimezone(timezone).isoformat(),
                        "primaryKey": 1
                    },
                    "actions": [
                        {"action": "", "title": "Abrir"}
                    ]
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

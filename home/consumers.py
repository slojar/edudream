import json

from channels.generic.websocket import WebsocketConsumer


class ClassroomConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def send_notification(self, message):
        self.send(text_data=json.dumps(message))

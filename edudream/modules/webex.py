import json
import logging

import requests
from django.conf import settings
from edudream.modules.utils import generate_random_password

api_key = settings.WEBEX_API_KEY
base_url = settings.WEBEX_BASE_URL


class WebexAPI:

    @classmethod
    def get_header(cls):
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    @classmethod
    def log_request(cls, *args):
        for arg in args:
            logging.info(arg)

    @classmethod
    def authorize(cls):
        url = f"{base_url}/authorize"
        param = {
            "response_type": "code",
            "client_id": "C278a4a61208eff910dad0c74f56f6ab2da9813dad45c216f93383ad930d1ce35",
            "redirect_uri": "https://edudream.fr",
            "scope": ["meeting:schedules_write"],
            "state": "test"
        }
        # cls.log_request(f"url: {url}\npayload: {payload}\n")
        response = requests.request("GET", url, params=param)
        cls.log_request(f"response: {response.text}")
        return response.json()

    @classmethod
    def create_meeting(cls, start_date, end_date, attending, **kwargs):
        url = f"{base_url}/meetings"
        header = cls.get_header()
        password = generate_random_password()
        guests = [{"email": item.get("email"), "displayName": item.get("name"), "coHost": False, "panelist": False} for item in attending]
        meeting = dict()
        meeting["invitees"] = guests
        meeting["title"] = kwargs.get("title")
        meeting["agenda"] = kwargs.get("narration")
        meeting["password"] = password
        meeting["start"] = start_date
        meeting["end"] = end_date
        meeting["sendEmail"] = False
        meeting["hostEmail"] = "info@edudream.fr"
        meeting["enabledJoinBeforeHost"] = True
        meeting["enableConnectAudioBeforeHost"] = True
        meeting["enabledBreakoutSessions"] = False

        payload = json.dumps(meeting)
        cls.log_request(f"url: {url}\npayload: {payload}\n")
        response = requests.request("POST", url, data=payload, headers=header)
        cls.log_request(f"response: {response.text}")
        return response.json()


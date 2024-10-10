import json

import requests
from django.conf import settings
from sentry_sdk import capture_message

from edudream.modules.utils import generate_random_password

# base_url = https://api.zoom.us/v2/users/me/meetings
base_url = settings.ZOOM_BASE_URL
zoom_email = settings.ZOOM_EMAIL


class ZoomAPI:

    @classmethod
    def get_header(cls):
        from edudream.modules.utils import get_site_details, decrypt_text
        return {"Authorization": f"Bearer {decrypt_text(get_site_details().zoom_token)}", "Content-Type": "application/json"}

    @classmethod
    def log_request(cls, *args):
        for arg in args:
            capture_message(str(arg), level="info")

    @classmethod
    def create_meeting(cls, start_date, duration, attending, **kwargs):
        url = f"{base_url}/users/me/meetings"
        header = cls.get_header()
        password = generate_random_password()
        guests = [{"email": item.get("email")} for item in attending]

        meeting = {
            "agenda": kwargs.get("narration"),
            "default_password": False,
            "duration": int(duration),
            "password": str(password),
            "pre_schedule": False,
            "schedule_for": str(zoom_email),
            "settings": {
                "additional_data_center_regions": [
                    "TY"
                ],
                "allow_multiple_devices": False,
                "approval_type": 2,
                "audio": "both",
                "auto_recording": "none",
                "breakout_room": {
                    "enable": False
                },
                "calendar_type": 1,
                "close_registration": False,
                "email_notification": True,
                "encryption_type": "enhanced_encryption",
                "focus_mode": False,
                "host_video": False,
                "jbh_time": 0,
                "join_before_host": True,
                "meeting_authentication": True,
                "meeting_invitees": guests,
                "mute_upon_entry": False,
                "participant_video": False,
                "private_meeting": False,
                "registration_type": 1,
                "show_share_button": True,
                "use_pmi": False,
                "waiting_room": False,
                "watermark": False,
                "host_save_video_order": True,
                "alternative_host_update_polls": True,
                "internal_meeting": False,
                "continuous_meeting_chat": {
                    "enable": True,
                    "auto_add_invited_external_users": True
                },
                "participant_focused_meeting": False,
                "push_change_to_calendar": False,
                "resources": [
                    {
                        "resource_type": "whiteboard",
                        "resource_id": password,
                        "permission_level": "editor"
                    }
                ]
            },
            "start_time": start_date,
            "timezone": "Europe/Paris",
            "topic": kwargs.get("title"),
            "type": 2
        }
        payload = json.dumps(meeting)
        cls.log_request(f"url: {url}\npayload: {payload}\n")
        response = requests.request("POST", url, data=payload, headers=header)
        cls.log_request(f"response: {response.text}")
        if response.status_code == 201:
            # response = response.json()
            # meeting_id = response["id"]
            # return response["join_url"]
            return response.json()
        else:
            return None

    @classmethod
    def end_meeting(cls, start_date, duration, meeting_id, **kwargs):
        url = f"{base_url}/meetings/{meeting_id}/status"
        header = cls.get_header()
        payload = {"action": "end"}
        cls.log_request(f"url: {url}\npayload: {payload}\n")
        response = requests.request("PUT", url, data=payload, headers=header)
        cls.log_request(f"response: {response.text}")
        return True



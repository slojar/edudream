import json
import logging
import datetime

import requests
from django.conf import settings
from edudream.modules.utils import generate_random_password

# base_url = https://api.zoom.us/v2/users/me/meetings
base_url = settings.ZOOM_BASE_URL
zoom_email = settings.ZOOM_EMAIL

toktn = "eyJzdiI6IjAwMDAwMSIsImFsZyI6IkhTNTEyIiwidiI6IjIuMCIsImtpZCI6ImUxNTczNGVhLWNlNDYtNDVlZi04MmE5LWU4OWUxNjFjMjE5NiJ9.eyJhdWQiOiJodHRwczovL29hdXRoLnpvb20udXMiLCJ1aWQiOiIzX2lpZ3c2VlRNVzcyOUdWeW1lUUZRIiwidmVyIjo5LCJhdWlkIjoiNzkxZjY0YjVkOTYyN2MyYTgyYjg2OTQ4NWM2MTdiMDYiLCJuYmYiOjE3MDc5NDIwNzYsImNvZGUiOiI1eVpSbWpOTVMyT01zaUkwV1Q3UFVnd2pTdHBPcTVXOHAiLCJpc3MiOiJ6bTpjaWQ6aG1mVkJZdzJUQkMxQVBWb0xHNzhNdyIsImdubyI6MCwiZXhwIjoxNzA3OTQ1Njc2LCJ0eXBlIjozLCJpYXQiOjE3MDc5NDIwNzYsImFpZCI6ImtJeGNNQXBvVHh1bG40NzRpSVkzRmcifQ.BxsPQ8YamozCKX6SWgtcrEesfpBGCAu5PP6PqhoYcClyJ0tsknDEq6oNL6N_ton7RX_b0boX4rgEbJPLXhvEig"


class ZoomAPI:

    @classmethod
    def get_header(cls):
        from edudream.modules.utils import get_site_details, decrypt_text
        # return {"Authorization": f"Bearer {decrypt_text(get_site_details().zoom_token)}",
        return {"Authorization": f"Bearer {toktn}",
                "Content-Type": "application/json"}

    @classmethod
    def log_request(cls, *args):
        for arg in args:
            logging.info(arg)

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
            response = response.json()
            return response["join_url"]
        else:
            return None

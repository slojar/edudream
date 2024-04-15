import requests
from django.conf import settings


base_url = settings.TRANSLATOR_URL
api_key = settings.RAPID_API_KEY
api_host = settings.RAPID_API_HOST


class Translate:
    @classmethod
    def perform_translate(cls, to_lang, content):
        from edudream.modules.utils import log_request
        url = f"{base_url}?langpair=en|{to_lang}&q={content}"
        header = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api_host
        }
        response = requests.request("GET", url, headers=header)
        log_request(f"Translation Response: {response.text}")
        text_to_return = content
        if response.status_code == 200:
            result = response.json()
            text_to_return = result["responseData"]["translatedText"]
        return text_to_return


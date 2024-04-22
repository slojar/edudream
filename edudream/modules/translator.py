import json

import requests
from django.conf import settings


base_url = settings.TRANSLATOR_URL
deep_base_url = settings.DEEP_BASE_URL
deep_api_key = settings.DEEP_API_KEY
api_key = settings.RAPID_API_KEY
api_host = settings.RAPID_API_HOST


class Translate:
    @classmethod
    def perform_translate_rapid(cls, to_lang, content):
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

    @classmethod
    def perform_translate_deepl(cls, to_lang, content):
        from edudream.modules.utils import log_request
        url = f"{deep_base_url}"
        header = {"Content-Type": "application/json", "Authorization": f"DeepL-Auth-Key {deep_api_key}"}
        payload = json.dumps({"text": [str(content)], "target_lang": str(to_lang).upper()})
        response = requests.request("POST", url, headers=header, data=payload)
        log_request(f"Translation Response: {response.text}")
        text_to_return = content
        if response.status_code == 200:
            result = response.json()
            text_to_return = result["translations"][0]["text"]
        return text_to_return



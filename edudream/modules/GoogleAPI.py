import json
import os

from django.conf import settings
from google.auth.transport import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from edudream.modules.utils import log_request


def generate_meeting_link(meeting_name, attending, request_id, **kwargs):
    scope = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"]

    auth_file = 'edudream.json'

    credential = None

    if os.path.exists('calender_auth.json'):
        credential = Credentials.from_authorized_user_file('calender_auth.json', scope)

    # If there are no (valid) credentials available, let the user log in.
    if not credential or not credential.valid:
        if credential and credential.expired and credential.refresh_token:
            credential.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(auth_file, scope)
            credential = flow.run_local_server(host=settings.GOOGLE_REDIRECT_URL)
        # Save the credentials for the next run
        with open('calender_auth.json', 'w') as token:
            token.write(credential.to_json())

    event = dict()
    default_timezone = ""
    guests = [{"email": email, "responseStatus": "needsAction"} for email in attending]

    event["creator"] = dict()
    event["creator"]["displayName"] = settings.APP_NAME
    event["creator"]["email"] = settings.COMPANY_ENQUIRY_EMAIL

    event["attendees"] = guests
    event["description"] = kwargs.get("narration")
    event["guestsCanModify"] = False
    event["guestsCanInviteOthers"] = False
    event["sendUpdates"] = "all"

    event["start"] = dict()
    event["start"]["dateTime"] = kwargs.get("start_date")
    event["start"]["timeZone"] = default_timezone

    event["end"] = dict()
    event["end"]["dateTime"] = kwargs.get("end_date")
    event["end"]["timeZone"] = default_timezone
    event["anyoneCanAddSelf"] = False
    event["summary"] = meeting_name

    event["conferenceData"] = dict()
    event["conferenceData"]["createRequest"] = dict()
    event["conferenceData"]["createRequest"]["conferenceSolutionKey"] = dict()
    event["conferenceData"]["createRequest"]["status"] = dict()
    event["conferenceData"]["createRequest"]["status"]["statusCode"] = "success"
    event["conferenceData"]["createRequest"]["conferenceSolutionKey"]["type"] = "hangoutsMeet"
    event["conferenceData"]["createRequest"]["requestId"] = request_id

    try:
        service = build('calendar', 'v3', credentials=credential)
        # GET CALENDAR LIST
        # page_token = None
        # while True:
        #     calendar_list = service.calendarList().list(pageToken=page_token).execute()
        #     for calendar_list_entry in calendar_list['items']:
        #         print(calendar_list_entry['summary'])
        #     page_token = calendar_list.get('nextPageToken')
        #     if not page_token:
        #         break

        # CREATE CALENDAR
        # calendar = {
        #   'summary': 'Celeb Meet',
        #   'timeZone': 'America/Los_Angeles'
        # }
        # created_calendar = service.calendars().insert(body=calendar).execute()
        # print(created_calendar['id'])

        # CREATE EVENT
        created_event = service.events().insert(
            calendarId=settings.CALENDAR_ID, body=event, conferenceDataVersion=1,
            maxAttendees=2, sendNotifications=True).execute()
        log_request(f"Creating Google Event\n{created_event}")

        meet_link = created_event['hangoutLink']
        # print(meet_link)
    except Exception as error:
        log_request('CalendarAPI error: %s' % error)
        meet_link = None

    # Return the meet link
    return meet_link

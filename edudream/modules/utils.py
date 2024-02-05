import base64
import calendar
import datetime
import logging
import re
import secrets

from django.contrib.sites.models import Site
from django.utils import timezone
import requests
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils.crypto import get_random_string
from dateutil.relativedelta import relativedelta

from home.models import SiteSetting, Transaction
from location.models import City, State, Country

from edudream.modules.stripe_api import StripeAPI

email_from = settings.EMAIL_FROM
email_url = settings.EMAIL_URL
email_api_key = settings.EMAIL_API_KEY


def log_request(*args):
    for arg in args:
        logging.info(arg)


def format_phone_number(phone_number):
    phone_number = f"0{phone_number[-10:]}"
    return phone_number


def encrypt_text(text: str):
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    fernet = Fernet(key)
    secure = fernet.encrypt(f"{text}".encode())
    return secure.decode()


def decrypt_text(text: str):
    key = base64.urlsafe_b64encode(settings.SECRET_KEY.encode()[:32])
    fernet = Fernet(key)
    decrypt = fernet.decrypt(text.encode())
    return decrypt.decode()


def generate_random_password():
    return get_random_string(length=10)


def generate_random_otp():
    return get_random_string(length=6, allowed_chars="1234567890")


def get_previous_date(date, delta):
    previous_date = date - relativedelta(days=delta)
    return previous_date


def get_next_date(date, delta):
    next_date = date + relativedelta(days=delta)
    return next_date


def get_next_minute(date, delta):
    next_minute = date + relativedelta(minutes=delta)
    return next_minute


def get_previous_minute(date, delta):
    previous_minute = date - relativedelta(minutes=delta)
    return previous_minute


def get_previous_seconds(date, delta):
    # previous_seconds = date - datetime.timedelta(seconds=delta)
    previous_seconds = date - relativedelta(seconds=delta)
    return previous_seconds


def get_previous_hour(date, delta):
    previous_hour = date - relativedelta(hours=delta)
    return previous_hour


def get_day_start_and_end_datetime(date_time):
    day_start = date_time - relativedelta(day=0)
    # day_end = day_start + relativedelta(day=0)
    day_end = day_start + relativedelta(days=1)
    day_start = day_start.date()
    # day_start = datetime.datetime.combine(day_start.date(), datetime.time.min)
    # day_end = datetime.datetime.combine(day_end.date(), datetime.time.max)
    day_end = day_end.date()
    return day_start, day_end


def get_week_start_and_end_datetime(date_time):
    week_start = date_time - datetime.timedelta(days=date_time.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_start = datetime.datetime.combine(week_start.date(), datetime.time.min)
    week_end = datetime.datetime.combine(week_end.date(), datetime.time.max)
    return week_start, week_end


def get_month_start_and_end_datetime(date_time):
    month_start = date_time.replace(day=1)
    month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
    month_start = datetime.datetime.combine(month_start.date(), datetime.time.min)
    month_end = datetime.datetime.combine(month_end.date(), datetime.time.max)
    return month_start, month_end


def get_year_start_and_end_datetime(date_time):
    year_start = date_time.replace(day=1, month=1, year=date_time.year)
    year_end = date_time.replace(day=31, month=12, year=date_time.year)
    year_start = datetime.datetime.combine(year_start.date(), datetime.time.min)
    year_end = datetime.datetime.combine(year_end.date(), datetime.time.max)
    return year_start, year_end


def get_previous_month_date(date, delta):
    return date - relativedelta(months=delta)


def get_next_month_date(date, delta):
    return date + relativedelta(months=delta)


def send_email(content, email, subject):
    payload = {
        "key": email_api_key,
        "message": {"text": content, "subject": subject, "from_email": email_from, "from_name": "",
                    "to": [{"email": email, "name": ""}]}
    }
    response = requests.request("POST", email_url, headers={'Content-Type': 'application/json'}, data=payload)
    log_request(f"Sending email to: {email}, Response: {response.text}")
    return response.text


def incoming_request_checks(request, require_data_field: bool = True) -> tuple:
    try:
        x_api_key = request.headers.get('X-Api-Key', None) or request.META.get("HTTP_X_API_KEY", None)
        request_type = request.data.get('requestType', None)
        data = request.data.get('data', {})

        if not x_api_key:
            return False, "Missing or Incorrect Request-Header field 'X-Api-Key'"

        if x_api_key != settings.X_API_KEY:
            return False, "Invalid value for Request-Header field 'X-Api-Key'"

        if not request_type:
            return False, "'requestType' field is required"

        if request_type != "inbound":
            return False, "Invalid 'requestType' value"

        if require_data_field:
            if not data:
                return False, "'data' field was not passed or is empty. It is required to contain all request data"

        return True, data
    except (Exception,) as err:
        return False, f"{err}"


def get_incoming_request_checks(request) -> tuple:
    try:
        x_api_key = request.headers.get('X-Api-Key', None) or request.META.get("HTTP_X_API_KEY", None)

        if not x_api_key:
            return False, "Missing or Incorrect Request-Header field 'X-Api-Key'"

        if x_api_key != settings.X_API_KEY:
            return False, "Invalid value for Request-Header field 'X-Api-Key'"

        return True, ""
        # how do I handle requestType and also client ID e.g 'inbound', do I need to expect it as a query parameter.
    except (Exception,) as err:
        return False, f"{err}"


def api_response(message, status: bool, data=None, **kwargs) -> dict:
    if data is None:
        data = {}
    try:
        reference_id = secrets.token_hex(30)
        response = dict(requestTime=timezone.now(), requestType='outbound', referenceId=reference_id,
                        status=status, message=message, data=data, **kwargs)

        # if "accessToken" in data and 'refreshToken' in data:
        if "accessToken" in data:
            # Encrypting tokens to be
            response['data']['accessToken'] = encrypt_text(text=data['accessToken'])
            # response['data']['refreshToken'] = encrypt_text(text=data['refreshToken'])
            logging.info(msg=response)

            response['data']['accessToken'] = decrypt_text(text=data['accessToken'])
            # response['data']['refreshToken'] = encrypt_text(text=data['refreshToken'])

        else:
            logging.info(msg=response)

        return response
    except (Exception,) as err:
        return err


def password_checker(password: str):
    try:
        # Python program to check validation of password
        # Module of regular expression is used with search()

        flag = 0
        while True:
            if len(password) < 8:
                flag = -1
                break
            elif not re.search("[a-z]", password):
                flag = -1
                break
            elif not re.search("[A-Z]", password):
                flag = -1
                break
            elif not re.search("[0-9]", password):
                flag = -1
                break
            elif not re.search("[#!_@$-]", password):
                flag = -1
                break
            elif re.search("\s", password):
                flag = -1
                break
            else:
                flag = 0
                break

        if flag == 0:
            return True, "Valid Password"

        return False, "Password must contain uppercase, lowercase letters, '# ! - _ @ $' special characters " \
                      "and 8 or more characters"
    except (Exception,) as err:
        return False, f"{err}"


def validate_email(email):
    try:
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.fullmatch(regex, email):
            return True
        return False
    except (TypeError, Exception) as err:
        # Log error
        return False


def get_country_id_by_currency_code(currency_code):
    country = Country.objects.filter(currency_code__iexact=currency_code).first()
    if country:
        return country.id
    return None


def create_country(country):
    country_name = country["name"]
    new_country = Country.objects.filter(name__iexact=country_name).last()

    if not new_country:
        short_name2 = country["iso2"]
        short_name3 = country["iso3"]
        currency_name = country["currency_name"]
        currency_code = country["currency"]
        currency_symbol = country["currency_symbol"]
        dialing_code = country["phone_code"]
        flag = country["emojiU"]

        new_country = Country.objects.create(
            name=country_name, alpha2code=short_name2, alpha3code=short_name3, currency_name=currency_name,
            currency_code=currency_code, currency_symbol=currency_symbol, calling_code=dialing_code, flag_link=flag
        )

    return new_country


def create_state(state, new_country):
    state_name = state["name"]
    new_state = State.objects.filter(country=new_country, name__iexact=state_name).last()
    if not new_state:
        state_code = state["state_code"]
        new_state = State.objects.create(country=new_country, name=state_name, code=state_code)

    return new_state


def create_country_state_city():
    url = "https://raw.githubusercontent.com/slojar/countries-states-cities-database/master/countries%2Bstates%2Bcities.json"
    response = requests.request("GET", url).json()
    for country in response:
        new_country = create_country(country)
        states = country["states"]
        for state in states:
            new_state = create_state(state, new_country)
            cities = state["cities"]
            for city in cities:
                city_name = city["name"]
                if not City.objects.filter(state=new_state, name__exact=city_name).exists():
                    latitude = city["latitude"]
                    longitude = city["longitude"]
                    City.objects.create(state=new_state, name=city_name, longitude=longitude, latitude=latitude)

    return True


def get_site_details():
    try:
        site, created = SiteSetting.objects.get_or_create(site=Site.objects.get_current())
    except Exception as ex:
        logging.exception(str(ex))
        site = SiteSetting.objects.filter(site=Site.objects.get_current()).first()
    return site


def complete_payment(ref_number):
    try:
        trans = Transaction.objects.get(reference=ref_number, status="pending")
    except Transaction.DoesNotExist:
        return False, f'Reference Number ({ref_number}) not found'

    reference = str(ref_number)

    if str(ref_number).lower().startswith('cs_'):
        try:
            result = StripeAPI.retrieve_checkout_session(session_id=reference)
            reference = result.get('payment_intent')
        except Exception as ex:
            logging.error(ex)
            pass

    result = dict()
    if str(reference).lower().startswith('pi_'):
        result = StripeAPI.retrieve_payment_intent(payment_intent=reference)
    if str(reference).lower().startswith('cs_'):
        result = StripeAPI.retrieve_checkout_session(session_id=reference)

    if result.get('status') and str(result.get('status')).lower() in ['succeeded', 'success', 'successful']:
        trans.status = "completed"
        trans.save()

        if trans.transaction_type == "fund_wallet":
            # Add coin equivalent of Payment Plan to Wallet balance
            customer_wallet = trans.user.wallet
            customer_wallet.refresh_from_db()
            customer_wallet.balance += trans.plan.coin
            customer_wallet.save()
            # Confirm if this is customer's first deposit, and credit referrer
            first_fund_wallet = Transaction.objects.filter(transaction_type="fund_wallet", status="completed").first()
            referrer = trans.user.profile.referred_by
            if first_fund_wallet == trans and referrer is not None:
                referral_point = get_site_details().referral_coin
                referrer_wallet = referrer.wallet
                referrer_wallet.refresh_from_db()
                referrer_wallet.balance += referral_point
                referrer_wallet.save()
                # Create Referral Transaction
                Transaction.objects.create(
                    user=referrer, transaction_type="bonus", amount=referral_point, status="completed",
                    narration=f"Referal bonus from {trans.user.get_full_name()}"
                )
                # Send notification to referrer
            # Send Notification to user

        return True, "Payment updated"
    else:
        trans.status = "failed"
        trans.save()
        return False, ""










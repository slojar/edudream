import datetime

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import decrypt_text
from home.models import Transaction
from tutor.models import PayoutRequest

zoom_auth_url = settings.ZOOM_AUTH_URL
zoom_client_id = settings.ZOOM_CLIENT_ID
zoom_client_secret = settings.ZOOM_CLIENT_SECRET


def zoom_login_refresh():
    url = zoom_auth_url
    response = requests.request("POST", url=url, auth=HTTPBasicAuth(str(zoom_client_id), str(zoom_client_secret)))
    return response.json()


def payout_cron_job():
    last_7_days = datetime.datetime.now() - datetime.timedelta(days=7)
    payouts = PayoutRequest.objects.filter(status="pending", created_on__gte=last_7_days)
    for instance in payouts:
        amount = float(instance.amount)
        # Check stripe balance
        # balance = StripeAPI.get_account_balance()
        # new_balance = float(balance / 100)
        # if amount > new_balance:
        #     break
            # raise InvalidRequestException({"detail": "Cannot process payout at the moment, please try again later"})
        stripe_connect_account_id = decrypt_text(instance.user.profile.stripe_connect_account_id)
        narration = f"EduDream Payout of EUR{amount} to {instance.user.get_full_name()}"

        # Process Transfer
        response = StripeAPI.transfer_to_connect_account(amount=amount, acct=stripe_connect_account_id, desc=narration)
        payout_trx_ref = response.get("id")
        instance.reference = payout_trx_ref
        # Create Transaction
        transaction = Transaction.objects.create(
            user=instance.user, transaction_type="withdrawal", amount=amount, narration=narration
        )
        stripe_external_account_id = decrypt_text(instance.bank_account.stripe_external_account_id)
        payout_response = StripeAPI.payout_to_external_account(amount=amount, acct=stripe_external_account_id)
        if payout_response.get("failure_message") is None and payout_response.get("id"):
            instance.status = "processed"
            transaction.status = "completed"
            transaction.reference = str(payout_response.get("id"))
            # Send payout email
        # Update transaction/payout status
        instance.save()
        transaction.save()

    return True


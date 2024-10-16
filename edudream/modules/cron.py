from threading import Thread

import requests
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from edudream.modules.email_template import send_class_reminder_email, send_fund_pending_balance_email, \
    send_fund_main_balance_email, send_class_ended_reminder_email, student_class_declined_email, \
    auto_classroom_complete_email
from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import log_request, get_site_details
from tutor.models import PayoutRequest, Classroom, TutorCalendar

zoom_auth_url = settings.ZOOM_AUTH_URL
zoom_client_id = settings.ZOOM_CLIENT_ID
zoom_client_secret = settings.ZOOM_CLIENT_SECRET


def zoom_login_refresh():
    url = zoom_auth_url
    response = requests.request("POST", url=url, auth=HTTPBasicAuth(str(zoom_client_id), str(zoom_client_secret)))
    return response.json()


def payout_cron_job():
    # This cron to run every 60 minute
    payouts = PayoutRequest.objects.filter(status="pending")
    try:
        for instance in payouts:
            stripe_connect_account_id = instance.user.profile.stripe_connect_account_id
            stripe_external_account_id = instance.bank_account.stripe_external_account_id
            amount = float(instance.amount)
            # Check stripe balance
            payout_response = StripeAPI.payout_to_external_account(
                amount=amount, acct=stripe_external_account_id, stripe_acct=stripe_connect_account_id
            )
            if payout_response.get("failure_message") is None and payout_response.get("id"):
                instance.status = "processed"
                instance.reference = str(payout_response.get("id"))
                instance.transaction.status = "completed"
                # Send payout email
                # Update transaction/payout status
                instance.save()
                instance.transaction.save()
                Thread(target=send_class_reminder_email, args=[instance.user, amount, "fr"]).start()
    except Exception as err:
        log_request(f"Error processing payouts: {err}")

    return True


def class_reminder_job():
    # This cron to run every minute
    now = timezone.now()
    notification_60min_time = now + timezone.timedelta(minutes=60)
    notification_15min_time = now + timezone.timedelta(minutes=15)
    notification_0min_time = now

    classrooms_60min = Classroom.objects.filter(status="accepted", start_date=notification_60min_time)
    classrooms_15min = Classroom.objects.filter(status="accepted", start_date=notification_15min_time)
    classrooms_0min = Classroom.objects.filter(status="accepted", start_date=notification_0min_time)

    # Just ended classes
    ended_classes = Classroom.objects.filter(status="accepted", end_date__minute=now.minute, end_date__hour=now.hour)
    # Unattended classes
    unattended_classes = Classroom.objects.filter(status="new", start_date__minute=now.minute, start_date__hour=now.hour)
    # All Ended Classes
    all_ended_classes = Classroom.objects.filter(end_date__lte=now)

    if classrooms_60min:
        # Send 60 minute reminder
        for class_room in classrooms_60min:
            student_user = class_room.student.user
            Thread(target=send_class_reminder_email, args=[student_user, class_room, 60, "fr"]).start()
    if classrooms_15min:
        # Send 15 minute reminder
        for class_room in classrooms_15min:
            student_user = class_room.student.user
            Thread(target=send_class_reminder_email, args=[student_user, class_room, 15, "fr"]).start()
    if classrooms_0min:
        # Send 0 minute reminder
        for class_room in classrooms_0min:
            student_user = class_room.student.user
            Thread(target=send_class_reminder_email, args=[student_user, class_room, 0, "fr"]).start()

    if ended_classes:
        # Send ended class reminder
        for class_room in ended_classes:
            # Remove classroom from all schedules
            class_room.tutorcalendar_set.all().update(status="available")
            for tutor_calendar in class_room.tutorcalendar_set.all():
                tutor_calendar.classroom.clear()

            student_email = class_room.student.user.email
            parent_email = class_room.student.parent.user.email
            tutor_email = class_room.tutor.email
            Thread(target=send_class_ended_reminder_email, args=[student_email, class_room, "fr"]).start()
            Thread(target=send_class_ended_reminder_email, args=[tutor_email, class_room, "fr"]).start()
            Thread(target=send_class_ended_reminder_email, args=[parent_email, class_room, "fr"]).start()

    if unattended_classes:
        for class_room in unattended_classes:
            # Set classroom status as declined
            class_room.status = "declined"
            class_room.save()
            if TutorCalendar.objects.filter(classroom=class_room).exists():
                t_calendar = TutorCalendar.objects.filter(classroom=class_room).last()
                t_calendar.classroom.clear()
                t_calendar.status = "available"
                t_calendar.save()
            Thread(target=student_class_declined_email, args=[class_room, "fr"]).start()

    if all_ended_classes:
        # Remove ended classroom from calendar
        for class_room in all_ended_classes:
            if TutorCalendar.objects.filter(classroom=class_room).exists():
                t_calendar = TutorCalendar.objects.filter(classroom=class_room).last()
                t_calendar.classroom.clear()
                t_calendar.status = "available"
                t_calendar.save()

    return True


def class_fee_to_tutor_pending_balance_job():
    # This cron to run every 60 minute
    classrooms = Classroom.objects.filter(status="completed", pending_balance_paid=False)
    # Update tutor wallet with class coin/amount
    try:
        now = timezone.now()
        next_5_days = now + timezone.timedelta(days=5)
        d_site = get_site_details()
        for classroom in classrooms:
            amount = classroom.amount
            user_wallet = classroom.tutor.wallet
            esrow_balance = d_site.escrow_balance
            # Subtract from escrow balance
            esrow_balance -= amount
            user_wallet.refresh_from_db()
            # Add to tutor's pending balance
            user_wallet.pending += amount
            user_wallet.save()
            classroom.pending_balance_paid = True
            classroom.tutor_payment_expected = next_5_days
            classroom.save()
            # Send fund on the way email to tutor
            Thread(target=send_fund_pending_balance_email, args=[classroom.tutor, classroom, "fr"]).start()
    except Exception as err:
        log_request(f"Error processining pending fund {err}")

    return True


def process_pending_balance_to_main_job():
    # This cron to run every 4 hrs
    now = timezone.now()
    classrooms = Classroom.objects.filter(
        status="completed", pending_balance_paid=True, tutor_payment_expected__lte=now, tutor_paid=False
    )
    try:
        for classroom in classrooms:
            amount = classroom.amount
            user_wallet = classroom.tutor.wallet
            user_wallet.refresh_from_db()
            # Subtract amount from pending balance
            user_wallet.pending -= amount
            # Add amount to main balance
            user_wallet.balance += amount
            user_wallet.save()
            classroom.tutor_paid = True
            classroom.save()
            # Send classroom payment email to tutor
            Thread(target=send_fund_main_balance_email, args=[classroom.tutor, classroom, "fr"]).start()
    except Exception as err:
        log_request(f"Error occurred while processing pending balance to main: {err}")
    return True


def update_ended_classroom_jobs():
    # This cron to run every 1 hrs
    query = Q(tutor_complete_check=True) | Q(student_complete_check=True)
    now = timezone.now()
    ended_classrooms = Classroom.objects.filter(query, status="accepted", end_date__lte=now)
    # Mark classes as completed
    if ended_classrooms:
        ended_classrooms.update(status="completed")
        # Send email and notification
        for classroom in ended_classrooms:
            Thread(target=auto_classroom_complete_email, args=[classroom.tutor, classroom, "fr"]).start()

    # Check for all past classes
    last_24hrs = now - timezone.timedelta(hours=24)
    past_classes = Classroom.objects.filter(status="accepted", end_date__lte=last_24hrs)
    if past_classes:
        past_classes.update(status="completed")
        # Send email and notification
        for classroom in ended_classrooms:
            Thread(target=auto_classroom_complete_email, args=[classroom.tutor, classroom, "fr"]).start()

    return True





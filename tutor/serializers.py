import datetime
import decimal
import uuid
from threading import Thread

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from edudream.modules.GoogleAPI import generate_meeting_link
from edudream.modules.choices import ACCEPT_DECLINE_STATUS, DISPUTE_TYPE_CHOICES, DAY_OF_THE_WEEK_CHOICES, \
    AVAILABILITY_STATUS_CHOICES
from edudream.modules.email_template import tutor_class_creation_email, parent_class_creation_email, \
    tutor_class_approved_email, student_class_approved_email, student_class_declined_email, parent_class_cancel_email, \
    student_class_cancel_email, parent_low_threshold_email, payout_request_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.utils import get_site_details
from home.models import Subject, Transaction
from student.models import Student
from tutor.models import TutorDetail, Classroom, Dispute, TutorCalendar, TutorBankAccount, PayoutRequest


class TutorDetailSerializerOut(serializers.ModelSerializer):
    language = serializers.CharField(source="language.name")
    bank_accounts = serializers.SerializerMethodField()

    def get_bank_accounts(self, obj):
        return TutorBankAccountSerializerOut(TutorBankAccount.objects.filter(user=obj.user), many=True).data

    class Meta:
        model = TutorDetail
        exclude = ["user"]


class ClassRoomSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        exclude = []


class CreateClassSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # Logged in student
    name = serializers.CharField()
    description = serializers.CharField()
    tutor_id = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    subject_id = serializers.IntegerField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        name = validated_data.get("name")
        description = validated_data.get("description")
        tutor_id = validated_data.get("tutor_id")
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        subject_id = validated_data.get("subject_id")

        tutor = get_object_or_404(TutorDetail, user__id=tutor_id)
        subject = get_object_or_404(Subject, id=subject_id)
        student = get_object_or_404(Student, user=user)
        tutor_user = tutor.user
        d_site = get_site_details()

        # Check Tutor Calendar
        date_convert = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        if not TutorCalendar.objects.filter(user=tutor_user, day_of_the_week=date_convert.isoweekday(), time_from__hour=date_convert.hour, status="available"):
            raise InvalidRequestException({"detail": "Tutor is not available at the selected period"})

        # Check Tutor availability
        if Classroom.objects.filter(start_date__gte=start_date, end_date__lte=end_date, status__in=["new", "accepted"]).exists():
            raise InvalidRequestException({"detail": "Period booked by another user, please select another period"})

        # Check parent balance is available for class amount
        balance = user.parent.wallet.balance
        if subject.amount > balance:
            raise InvalidRequestException({"detail": "Insufficient balance, please top-up wallet"})

        # Check if call occurred earlier. If yes, then add tutor rest period to start time

        # Add grace period
        new_end_time = end_date + timezone.timedelta(minutes=int(d_site.class_grace_period))
        # Create class for student
        classroom = Classroom.objects.create(
            name=name, description=description, tutor=tutor_user, student=student, start_date=start_date,
            end_date=new_end_time, amount=subject.amount, subjects=subject
        )
        # Notify Tutor of created class
        Thread(target=tutor_class_creation_email, args=[classroom]).start()
        # Notify Parent of created class
        Thread(target=parent_class_creation_email, args=[classroom]).start()

        return ClassRoomSerializerOut(classroom, context={"request": self.context.get("request")}).data


class ApproveDeclineClassroomSerializerIn(serializers.Serializer):
    action = serializers.ChoiceField(choices=ACCEPT_DECLINE_STATUS)
    decline_reason = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        action = validated_data.get("action")
        decline_reason = validated_data.get("decline_reason")
        amount = instance.amount
        parent = instance.student.parent.user
        student = instance.student.user
        parent_wallet = parent.wallet

        d_site = get_site_details()

        if action == "accept":
            # Generate meeting link
            meeting_id = str(uuid.uuid4())
            tutor_email = instance.tutor.email
            student_email = student.email
            link = generate_meeting_link(
                meeting_name=f"{instance.name}", attending=[tutor_email, student_email], request_id=meeting_id,
                narration=instance.description, start_date=instance.start_date, end_date=instance.end_date
            )
            instance.status = "accepted"
            instance.meeting_link = link
            # Debit parent wallet
            parent_wallet.refresh_from_db()
            parent_wallet.balance -= amount
            parent_wallet.save()
            # Check parent new wallet balance and compare coin threshold
            parent_wallet.refresh_from_db()
            if parent_wallet.balance < d_site.coin_threshold:
                # Send low coin threshold email to parent
                Thread(target=parent_low_threshold_email, args=[parent, parent_wallet.balance]).start()

            # Add amount to Escrow Balance
            d_site.refresh_from_db()
            d_site.escrow_balance += amount
            d_site.save()
            # Create transaction
            Transaction.objects.create(
                user=parent, transaction_type="course_payment", amount=amount, narration=instance.description,
                status="completed"
            )
            # Send meeting link to student
            Thread(target=student_class_approved_email, args=[instance]).start()
            # Send notification to parent
            # Send meeting link to tutor
            Thread(target=tutor_class_approved_email, args=[instance]).start()
        elif action == "cancel":
            # Check if instance was initially in accepted state
            if not instance.status == "accepted":
                raise InvalidRequestException({"detail": "You can only cancel class request you recently accepted"})
            # Cancel class
            instance.status = "cancelled"
            # Subtract amount from Escrow Balance
            d_site.refresh_from_db()
            d_site.escrow_balance -= amount
            d_site.save()
            # Refund parent coin
            parent_wallet.refresh_from_db()
            parent_wallet.balance += amount
            parent_wallet.save()
            # Create refund transaction
            Transaction.objects.create(
                user=parent, transaction_type="refund", amount=amount, narration=f"Refund, {instance.description}",
                status="completed"
            )
            # Notify parent and student
            Thread(target=parent_class_cancel_email, args=[parent, amount]).start()
            Thread(target=student_class_cancel_email, args=[student]).start()
        else:
            if not decline_reason:
                raise InvalidRequestException({"detail": "Kindly specify reason why you are declining this request"})
            # Update instance state
            instance.decline_reason = decline_reason
            instance.status = "declined"
            # Send notification to student
            Thread(target=student_class_declined_email, args=[instance]).start()
            # Send notification to parent
        instance.save()
        return ClassRoomSerializerOut(instance, context={"request": self.context.get("request")}).data


class DisputeSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        exclude = []


class DisputeSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    title = serializers.CharField(max_length=200, required=False)
    dispute_type = serializers.ChoiceField(choices=DISPUTE_TYPE_CHOICES)
    content = serializers.CharField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        title = validated_data.get("title")
        d_type = validated_data.get("dispute_type")
        content = validated_data.get("content")

        if not title:
            raise InvalidRequestException({"detail": "Title is required"})

        # Create Dispute
        dispute, _ = Dispute.objects.get_or_create(submitted_by=user, title=title)
        dispute.dispute_type = d_type
        dispute.content = content
        dispute.save()
        return DisputeSerializerOut(dispute, context=self.context.get("request")).data

    def update(self, instance, validated_data):
        d_type = validated_data.get("dispute_type", instance.dispute_type)
        content = validated_data.get("content", instance.content)
        instance.dispute_type = d_type
        instance.content = content
        instance.save()
        return DisputeSerializerOut(instance, context=self.context.get("request")).data


class TutorCalendarSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = TutorCalendar
        exclude = []


class TutorCalendarSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    week_day = serializers.ChoiceField(choices=DAY_OF_THE_WEEK_CHOICES)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    status = serializers.ChoiceField(choices=AVAILABILITY_STATUS_CHOICES)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        week_day = validated_data.get("week_day")
        start_period = validated_data.get("start_time")
        end_period = validated_data.get("end_time")
        avail_status = validated_data.get("status")

        avail, _ = TutorCalendar.objects.get_or_create(user=user, day_of_the_week=week_day, time_from=start_period)
        avail.time_to = end_period
        avail.status = avail_status
        avail.save()

        return TutorCalendarSerializerOut(avail).data


class TutorBankAccountSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = TutorBankAccount
        exclude = []


class TutorBankAccountSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    bank_name = serializers.CharField()
    account_name = serializers.CharField()
    account_number = serializers.CharField()
    account_type = serializers.CharField(required=False)
    routing_number = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        bank = validated_data.get("bank_name")
        acct_name = validated_data.get("account_name")
        acct_no = validated_data.get("account_number")
        acct_type = validated_data.get("account_type")
        routing_no = validated_data.get("routing_number")

        acct, _ = TutorBankAccount.objects.get_or_create(user=user, bank_name__iexact=bank, account_number=acct_no)
        acct.account_name = acct_name
        acct.account_type = acct_type
        acct.routing_number = routing_no
        acct.save()

        return TutorBankAccountSerializerOut(acct).data


class PayoutSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        exclude = []


class RequestPayoutSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    amount = serializers.FloatField()
    bank_account_id = serializers.IntegerField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        coin = validated_data.get("amount")
        bank_acct_id = validated_data.get("bank_account_id")
        user_wallet = user.wallet

        bank_acct = get_object_or_404(TutorBankAccount, user=user, id=bank_acct_id)
        # Check if user balance is enough for withdrawal request
        user_wallet.refresh_from_db()
        if coin > user_wallet.balance:
            raise InvalidRequestException({"detail": "Insufficient balance"})
        payout_ratio = get_site_details().payout_coin_to_amount
        amount = decimal.Decimal(coin) * payout_ratio
        # Create Payout Request
        payout = PayoutRequest.objects.create(user=user, bank_account=bank_acct, coin=coin, amount=amount)
        # Send Email to user
        Thread(target=payout_request_email, args=[user]).start()
        return PayoutSerializerOut(payout).data







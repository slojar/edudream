import decimal
from threading import Thread

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from edudream.modules.choices import SEND_NOTIFICATION_TYPE_CHOICES, APPROVE_OR_DECLINE_CHOICES, DISPUTE_STATUS_CHOICES, \
    ADD_SUBTRACT_ACTION_CHOICES
from edudream.modules.email_template import tutor_status_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import decrypt_text, get_site_details
from home.models import Notification, Transaction, SiteSetting
from home.serializers import TutorListSerializerOut, NotificationSerializerOut
from tutor.serializers import PayoutSerializerOut, DisputeSerializerOut


class TutorStatusSerializerIn(serializers.Serializer):
    active = serializers.BooleanField(required=False)
    declined = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        decline = validated_data.get("declined", False)
        tutor_detail = instance.user.tutordetail
        instance.active = validated_data.get("active", instance.active)
        if decline:
            tutor_detail.status = "declined"
            instance.active = False
        if instance.active:
            tutor_detail.status = "approved"
            instance.active = True
            # Send Email
            instance.approved_on = timezone.now()
            Thread(target=tutor_status_email, args=[instance.user]).start()
        instance.save()
        tutor_detail.save()
        return TutorListSerializerOut(instance, context={"request": self.context.get("request")}).data


class AdminLoginSerializerIn(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def create(self, validated_data):
        username = validated_data.get("username")
        password = validated_data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise InvalidRequestException({"detail": "Invalid login credentials"})

        return user


class NotificationSerializerIn(serializers.Serializer):
    users = serializers.ListSerializer(child=serializers.IntegerField(), required=False)
    message = serializers.CharField(max_length=500)
    send_type = serializers.ChoiceField(choices=SEND_NOTIFICATION_TYPE_CHOICES, required=False)

    def create(self, validated_data):
        users = validated_data.get("users")
        message = validated_data.get("message")
        send_type = validated_data.get("send_type")

        if not send_type and users:
            raise InvalidRequestException({"detail": "Either list of user or send type is required"})

        if send_type == "all":
            users_list = [user.id for user in User.objects.all()]
        elif send_type == "parent":
            users_list = [parent.id for parent in User.objects.filter(profile__account_type="parent")]
        elif send_type == "tutor":
            users_list = [tutor.id for tutor in User.objects.filter(profile__account_type="tutor")]
        elif send_type == "student":
            users_list = [student.id for student in User.objects.filter(student__isnull=False)]
        else:
            users_list = users

        notification, created = Notification.objects.get_or_create(
            message=message, users_type=send_type, admin_initiated=True
        )

        if users_list:
            notification.user.clear()
            for user_id in users_list:
                notification.user.add(user_id)

        return NotificationSerializerOut(notification).data


class AdminChangePasswordSerializerIn(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def create(self, validated_data):
        user = validated_data.get("user")
        old_password = validated_data.get("old_password")
        new_password = validated_data.get("new_password")
        confirm_password = validated_data.get("confirm_password")

        if not check_password(password=old_password, encoded=user.password):
            raise InvalidRequestException({"detail": "Incorrect old password"})

        try:
            validate_password(password=new_password)
        except Exception as err:
            raise InvalidRequestException({'detail': ', '.join(list(err))})

        if new_password != confirm_password:
            raise InvalidRequestException({"detail": "Passwords mismatch"})

        # Check if new and old passwords are the same
        if old_password == new_password:
            raise InvalidRequestException({"detail": "Same passwords cannot be used"})

        user.password = make_password(password=new_password)
        user.save()

        return "Password Changed Successful"


class ApproveDeclinePayoutSerializerIn(serializers.Serializer):
    action = serializers.ChoiceField(choices=APPROVE_OR_DECLINE_CHOICES)

    def update(self, instance, validated_data):
        action_status = validated_data.get("action")
        if action_status == "approved":
            amount = float(instance.amount)
            # Check stripe balance
            balance = StripeAPI.get_account_balance()
            new_balance = float(balance / 100)
            if amount > new_balance:
                raise InvalidRequestException({"detail": "Cannot process payout at the moment, please try again later"})
            stripe_connect_account_id = decrypt_text(instance.user.profile.stripe_connect_account_id)
            narration = f"EduDream Payout of EUR{amount} to {instance.user.get_full_name()}"

            # Process Transfer
            response = StripeAPI.transfer_to_connect_account(amount=amount, acct=stripe_connect_account_id, desc=narration)
            trx_ref = response.get("id")
            # Create Transaction
            Transaction.objects.create(
                user=instance.user, transaction_type="withdrawal", amount=amount, narration=narration, reference=trx_ref
            )
            # stripe_external_account_id = decrypt_text(instance.bank_account.stripe_external_account_id)
        instance.status = action_status
        instance.save()
        return PayoutSerializerOut(instance, context={"request": self.context.get("request")})


class DisputeStatusUpdateSerializerIn(serializers.Serializer):
    status = serializers.ChoiceField(choices=DISPUTE_STATUS_CHOICES)

    def update(self, instance, validated_data):
        instance.status = validated_data.get("status", instance.status)
        instance.save()
        return DisputeSerializerOut(instance, context={"request": self.context.get("request")}).data


class SiteSettingSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        exclude = ["site", "google_calendar_id", "google_redirect_url", "zoom_token"]


class UpdateSiteSettingsSerializerIn(serializers.Serializer):
    def update(self, instance, validated_data):
        instance.site_name = validated_data.get("site_name", instance.site_name)
        instance.coin_threshold = validated_data.get("coin_threshold", instance.coin_threshold)
        instance.referral_coin = validated_data.get("referral_coin", instance.referral_coin)
        instance.payout_coin_to_amount = validated_data.get("payout_coin_to_amount", instance.payout_coin_to_amount)
        instance.class_grace_period = validated_data.get("class_grace_period", instance.class_grace_period)
        instance.intro_call_duration = validated_data.get("intro_call_duration", instance.intro_call_duration)
        instance.enquiry_email = validated_data.get("enquiry_email", instance.enquiry_email)
        instance.save()
        return SiteSettingSerializerOut(instance, context={"request": self.context.get("request")})


class WalletBalanceUpdateSerializerIn(serializers.Serializer):
    amount = serializers.FloatField()
    action = serializers.ChoiceField(choices=ADD_SUBTRACT_ACTION_CHOICES)

    def update(self, instance, validated_data):
        action = validated_data.get("action")
        amount = decimal.Decimal(validated_data.get("amount"))

        site_detail = get_site_details()
        if action == "add":
            # Subtract from escrow balance and credit user wallet
            site_detail.escrow_balance -= amount
            instance.balance += amount
            # Create transaction
            Transaction.objects.create(
                user=instance.user, transaction_type="refund", amount=amount, status="completed",
                narration="Dispute resolution from admin"
            )
            # Create Notification
        else:
            # Subtract from user wallet and credit escrow balance
            instance.balance -= amount
            site_detail.escrow_balance += amount
            # Create Notification
        instance.save()
        site_detail.save()
        return "Wallet balance updated"




from threading import Thread

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from edudream.modules.choices import SEND_NOTIFICATION_TYPE_CHOICES, APPROVE_OR_DECLINE_CHOICES
from edudream.modules.email_template import tutor_status_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import decrypt_text
from home.models import Notification, Transaction
from home.serializers import TutorListSerializerOut, NotificationSerializerOut
from tutor.serializers import PayoutSerializerOut


class TutorStatusSerializerIn(serializers.Serializer):
    active = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance.active = validated_data.get("active", instance.active)
        if instance.active:
            # Send Email
            instance.approved_on = timezone.now()
            Thread(target=tutor_status_email, args=[instance.user]).start()
        instance.save()
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

        notification, created = Notification.objects.get_or_create(message=message)

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




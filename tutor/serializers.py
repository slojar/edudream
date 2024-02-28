import datetime
import decimal
from threading import Thread

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from edudream.modules.zoom import ZoomAPI
from edudream.modules.choices import ACCEPT_DECLINE_STATUS, DISPUTE_TYPE_CHOICES, DAY_OF_THE_WEEK_CHOICES, \
    AVAILABILITY_STATUS_CHOICES
from edudream.modules.email_template import tutor_class_creation_email, parent_class_creation_email, \
    tutor_class_approved_email, student_class_approved_email, student_class_declined_email, parent_class_cancel_email, \
    student_class_cancel_email, parent_low_threshold_email, payout_request_email, parent_intro_call_email, \
    tutor_intro_call_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import get_site_details, encrypt_text, decrypt_text, mask_number, log_request, \
    create_notification
from home.models import Subject, Transaction, Profile
from location.models import Country
from student.models import Student
from tutor.models import TutorDetail, Classroom, Dispute, TutorCalendar, TutorBankAccount, PayoutRequest, TutorSubject, \
    TutorSubjectDocument


class TutorDetailSerializerOut(serializers.ModelSerializer):
    bank_accounts = serializers.SerializerMethodField()
    diploma_file = serializers.SerializerMethodField()
    proficiency_test_file = serializers.SerializerMethodField()

    def get_proficiency_test_file(self, obj):
        request = self.context.get("request")
        if obj.proficiency_test_file:
            return request.build_absolute_uri(obj.proficiency_test_file.url)
        return None

    def get_diploma_file(self, obj):
        request = self.context.get("request")
        if obj.diploma_file:
            return request.build_absolute_uri(obj.diploma_file.url)
        return None

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
    student_id = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    subject_id = serializers.IntegerField()
    book_now = serializers.BooleanField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        name = validated_data.get("name")
        description = validated_data.get("description")
        tutor_id = validated_data.get("tutor_id")
        student_id = validated_data.get("student_id")
        start_date = str(validated_data.get("start_date"))
        # duration = validated_data.get("duration")
        end_date = str(validated_data.get("end_date"))
        subject_id = validated_data.get("subject_id")
        book_now = validated_data.get("book_now", False)
        parent_profile = None

        try:
            parent_profile = Profile.objects.get(user=user, account_type="parent")
        except Profile.DoesNotExist:
            pass

        if parent_profile:
            student = get_object_or_404(Student, id=student_id, parent__user=user)
        else:
            student = get_object_or_404(Student, user=user)

        tutor = get_object_or_404(TutorDetail, user_id=tutor_id)
        subject = get_object_or_404(Subject, id=subject_id)
        tutor_user = tutor.user
        d_site = get_site_details()

        # Get Duration
        start_date_convert = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S%z")
        end_date_convert = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S%z")
        time_difference = end_date_convert - start_date_convert
        duration = (time_difference.days * 24 * 60) + (time_difference.seconds / 60).__round__()

        if duration < 15 or duration > 120:
            raise InvalidRequestException({"detail": "Duration cannot be less than 15minutes or greater than 2hours"})

        # Check if duration does not exceed tutor max hour
        if duration > tutor_user.tutordetail.max_hour_class_hour:
            raise InvalidRequestException({"detail": "Duration cannot be greater than tutor teaching period"})

        # Check Tutor Calendar
        if not TutorCalendar.objects.filter(
                user=tutor_user, day_of_the_week=start_date_convert.isoweekday(),
                time_from__hour=start_date_convert.hour, status="available"
        ):
            raise InvalidRequestException({"detail": "Tutor is not available at the selected period"})

        # Calculate Class Amount
        subject_amount = subject.amount  # coin value per subject per hour
        class_amount = duration * subject_amount / 60

        # Check Tutor availability
        if Classroom.objects.filter(start_date__gte=start_date, end_date__lte=end_date,
                                    status__in=["new", "accepted"]).exists():
            raise InvalidRequestException({"detail": "Period booked by another user, please select another period"})

        # Check if call occurred earlier. If yes, then add tutor rest period to start time

        # Add grace period
        new_end_time = end_date_convert + timezone.timedelta(minutes=int(d_site.class_grace_period))

        if not book_now:
            return {
                "detail": "Classroom estimation complete",
                "data": {"student_name": str(user.get_full_name()).upper(), "level": subject.grade,
                         "subject": subject.name, "start_at": start_date, "end_at": end_date,
                         "duration": f"{duration} minutes", "total_coin": class_amount}
            }

        # Check parent balance is available for class amount
        balance = student.parent.user.wallet.balance
        if class_amount > balance:
            raise InvalidRequestException({"detail": "Insufficient balance, please top-up wallet"})

        # Create class for student
        classroom = Classroom.objects.create(
            name=name, description=description, tutor=tutor_user, student=student, start_date=start_date,
            end_date=new_end_time, amount=class_amount, subjects=subject, expected_duration=duration
        )
        # Notify Tutor of created class
        Thread(target=tutor_class_creation_email, args=[classroom]).start()
        # Notify Parent of created class
        Thread(target=parent_class_creation_email, args=[classroom]).start()
        Thread(target=create_notification, args=[parent_profile.user, f"New class created for student {student.user.get_full_name()}"]).start()
        Thread(target=create_notification, args=[tutor_user, f"You have a new class request from {student.user.get_full_name()}"]).start()

        return {
            "detail": "Classroom request sent successfully",
            "data": ClassRoomSerializerOut(classroom, context={"request": self.context.get("request")}).data
        }


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
            # meeting_id = str(uuid.uuid4())
            tutor_email = instance.tutor.email
            tutor_name = instance.tutor.get_full_name()
            student_name = student.get_full_name()
            student_email = student.email
            link = ZoomAPI.create_meeting(
                start_date=str(instance.start_date), duration=instance.expected_duration,
                attending=[{"name": str(student_name), "email": str(student_email)},
                           {"name": str(tutor_name), "email": str(tutor_email)}], narration=instance.description,
                title=instance.name
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
            Thread(target=create_notification, args=[student, f"Your class request has been approved by {tutor_name}"]).start()
            Thread(target=create_notification, args=[instance.tutor, f"You accepted a new class request with {student_name}"]).start()
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

        return TutorCalendarSerializerOut(avail, context={"request": self.context.get("request")}).data


class TutorBankAccountSerializerOut(serializers.ModelSerializer):
    account_number = serializers.SerializerMethodField()
    routing_number = serializers.SerializerMethodField()

    def get_routing_number(self, obj):
        if obj.routing_number:
            return mask_number(obj.routing_number, 5)
        return None

    def get_account_number(self, obj):
        if obj.account_number:
            return mask_number(obj.account_number, 5)
        return None

    class Meta:
        model = TutorBankAccount
        exclude = ["stripe_external_account_id"]


class TutorBankAccountSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    bank_name = serializers.CharField()
    account_name = serializers.CharField()
    account_number = serializers.CharField()
    account_type = serializers.CharField(required=False)
    routing_number = serializers.CharField()
    country_id = serializers.IntegerField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        bank = validated_data.get("bank_name")
        acct_name = validated_data.get("account_name")
        acct_no = validated_data.get("account_number")
        acct_type = validated_data.get("account_type")
        routing_no = validated_data.get("routing_number")
        country_id = validated_data.get("country_id")

        country = get_object_or_404(Country, id=country_id)
        tutor = get_object_or_404(Profile, user=user, account_type="tutor")

        try:

            if not tutor.stripe_connect_account_id:
                # Create Connect Account for Tutor
                connect_account = StripeAPI.create_connect_account(user)
                connect_account_id = connect_account.get("id")
                tutor.stripe_connect_account_id = encrypt_text(connect_account_id)
                tutor.save()

            stripe_connected_acct = decrypt_text(tutor.stripe_connect_account_id)

            # Add Bank Details to Connected Stripe Account
            external_account = StripeAPI.create_external_account(
                acct=stripe_connected_acct, account_no=acct_no, country_code=str(country.alpha2code).upper(),
                currency_code=str(country.currency_code).lower(), routing_no=routing_no
            )
            external_account_id = external_account.get("id")
            if external_account_id:
                acct, _ = TutorBankAccount.objects.get_or_create(user=user, bank_name=bank, account_number=acct_no)
                acct.account_name = acct_name
                acct.account_type = acct_type
                acct.routing_number = routing_no
                acct.country = country
                acct.stripe_external_account_id = encrypt_text(external_account_id)
                acct.save()

                return TutorBankAccountSerializerOut(acct, context={"request": self.context.get("request")}).data
            raise InvalidRequestException({"detail": "Could not validate account number, please try again later"})
        except Exception as err:
            log_request(f"Error while adding external bank account:\n{err}")
            raise InvalidRequestException({"detail": "An error has occurred, please try again later"})


class PayoutSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        exclude = []


class RequestPayoutSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # amount = serializers.FloatField()
    bank_account_id = serializers.IntegerField()
    request_now = serializers.BooleanField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        # coin = validated_data.get("amount")
        bank_acct_id = validated_data.get("bank_account_id")
        request_now = validated_data.get("request_now", False)
        user_wallet = user.wallet

        bank_acct = get_object_or_404(TutorBankAccount, user=user, id=bank_acct_id)
        # Check if user balance is enough for withdrawal request
        user_wallet.refresh_from_db()
        coin = user_wallet.balance
        payout_ratio = get_site_details().payout_coin_to_amount
        amount = decimal.Decimal(coin) * payout_ratio

        if not request_now:
            return {
                "detail": "Payout estimation complete",
                "data": {"name": str(user.get_full_name()).upper(), "wallet_balance": user_wallet.balance,
                         "coin_to_withdraw": coin, "amount_equivalent": f"EUR{amount}"}
            }
        # Create Payout Request
        payout = PayoutRequest.objects.create(user=user, bank_account=bank_acct, coin=coin, amount=amount)
        # Send Email to user
        Thread(target=payout_request_email, args=[user]).start()
        return {"detail": "Success", "data": PayoutSerializerOut(payout).data}


class TutorSubjectDocumentSerializerIn(serializers.ModelSerializer):
    class Meta:
        model = TutorSubjectDocument
        exclude = []


class TutorSubjectDocumentSerializerOut(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    def get_file(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url)

    class Meta:
        model = TutorSubjectDocument
        exclude = ["tutor_subject"]


class TutorSubjectSerializerOut(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    def get_documents(self, obj):
        request_context = {"request": self.context.get("request")}
        tutor_documents = TutorSubjectDocument.objects.filter(tutor_subject=obj)
        if tutor_documents.exists():
            return TutorSubjectDocumentSerializerOut(tutor_documents, many=True, context=request_context).data
        return None

    class Meta:
        model = TutorSubject
        exclude = []


class TutorSubjectSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    subject_id = serializers.IntegerField()
    tags = serializers.CharField(max_length=300, required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        subject_id = validated_data.get("subject_id")
        tag = validated_data.get("tags")

        subject = get_object_or_404(Subject, id=subject_id)

        # Create Subject Settings
        tutor_subject, _ = TutorSubject.objects.get_or_create(user=user, subject=subject)
        tutor_subject.tags = tag
        tutor_subject.save()

        return TutorSubjectSerializerOut(tutor_subject, context={"request": self.context.get("request")}).data


class IntroCallSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # Logged in student/parent
    tutor_id = serializers.IntegerField(help_text="Tutor User ID")
    student_id = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        tutor_id = validated_data.get("tutor_id")
        student_id = validated_data.get("student_id")
        start_date = str(validated_data.get("start_date"))
        parent_profile = None

        try:
            parent_profile = Profile.objects.get(user=user, account_type="parent")
        except Profile.DoesNotExist:
            pass

        if parent_profile:
            student = get_object_or_404(Student, id=student_id, parent__user=user)
        else:
            student = get_object_or_404(Student, user=user)

        tutor = get_object_or_404(TutorDetail, user_id=tutor_id)
        if not tutor.allow_intro_call:
            raise InvalidRequestException({"detail": "Tutor is not accepting intro call at the moment"})

        tutor_user = tutor.user
        d_site = get_site_details()

        # Calculate Call End Period
        call_duration = int(d_site.intro_call_duration)
        start_date_convert = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S%z")
        end_date = start_date_convert + datetime.timedelta(minutes=call_duration)
        # Check Tutor Calendar
        if not TutorCalendar.objects.filter(
                user=tutor_user, day_of_the_week=start_date_convert.isoweekday(),
                time_from__hour=start_date_convert.hour, status="available"
        ):
            raise InvalidRequestException({"detail": "Tutor is not available at the selected period"})

        # Check Tutor availability
        if Classroom.objects.filter(start_date__gte=start_date, end_date__lte=end_date,
                                    status__in=["new", "accepted"]).exists():
            raise InvalidRequestException({"detail": "Period booked by another user, please select another period"})

        tutor_email = tutor_user.email
        tutor_name = str("{} {}").format(tutor_user.first_name, tutor_user.last_name).upper()
        sender_email = student.user.email
        sender_name = student.user.get_full_name()
        if parent_profile:
            sender_email = parent_profile.email()
            sender_name = parent_profile.get_full_name()
        link = ZoomAPI.create_meeting(
            start_date=str(start_date_convert), duration=call_duration,
            attending=[{"name": str(sender_name), "email": str(sender_email)},
                       {"name": str(tutor_name), "email": str(tutor_email)}], narration=f"Intro call {tutor_name}",
            title=f"Intro call with {tutor_name}"
        )

        # Send invitation link to tutor, parent and/or student
        if link is not None:
            Thread(target=parent_intro_call_email, args=[user, tutor_name, start_date, end_date, link]).start()
            Thread(target=tutor_intro_call_email,
                   args=[tutor_user, user.get_full_name(), start_date, end_date, link]).start()

        return "Intro call booked successfully. Detail will be sent to your email address"
    # except Exception as err:
    #     log_request(f"Error while booking intro call\nError: {err}")
    #     raise InvalidRequestException({"detail": "Cannot process request at the moment. Please try again later"})

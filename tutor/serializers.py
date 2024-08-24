import datetime
import decimal
from threading import Thread

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers

from edudream.modules.zoom import ZoomAPI
from edudream.modules.choices import ACCEPT_DECLINE_STATUS, DISPUTE_TYPE_CHOICES
from edudream.modules.email_template import tutor_class_creation_email, parent_class_creation_email, \
    tutor_class_approved_email, student_class_approved_email, student_class_declined_email, parent_class_cancel_email, \
    student_class_cancel_email, parent_low_threshold_email, payout_request_email, parent_intro_call_email, \
    tutor_intro_call_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import get_site_details, encrypt_text, decrypt_text, mask_number, log_request, \
    create_notification, translate_to_language
from home.models import Subject, Transaction, Profile, ChatMessage
from location.models import Country
from student.models import Student
from tutor.models import TutorDetail, Classroom, Dispute, TutorCalendar, TutorBankAccount, PayoutRequest, TutorSubject, \
    TutorSubjectDocument


class TutorDetailSerializerOut(serializers.ModelSerializer):
    bank_accounts = serializers.SerializerMethodField()
    diploma_file = serializers.SerializerMethodField()
    proficiency_test_file = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()
    total_withdrawals = serializers.SerializerMethodField()
    future_payments = serializers.SerializerMethodField()

    def get_future_payments(self, obj):
        uncleared = Classroom.objects.filter(
            tutor=obj.user, status="completed", pending_balance_paid=False
        ).aggregate(Sum("amount"))["amount__sum"] or 0
        active = Classroom.objects.filter(
            tutor=obj.user, status="accepted"
        ).aggregate(Sum("amount"))["amount__sum"] or 0
        return {"uncleared": uncleared, "active_orders": active}

    def get_total_withdrawals(self, obj):
        data = dict()
        if PayoutRequest.objects.filter(user=obj.user).exists():
            payout = PayoutRequest.objects.filter(user=obj.user, status="processed")
            data["amount"] = payout.aggregate(Sum("amount"))["amount__sum"] or 0
            data["count"] = payout.count()
        else:
            data["amount"] = 0
            data["count"] = 0
        return data

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

    def get_subjects(self, obj):
        if TutorSubject.objects.filter(user=obj.user).exists():
            subject = TutorSubject.objects.filter(user=obj.user)
            return TutorSubjectSerializerOut(subject, many=True, context={"request": self.context.get("request")}).data
        return None

    class Meta:
        model = TutorDetail
        exclude = ["user"]


class ClassRoomSerializerOut(serializers.ModelSerializer):
    tutor = serializers.SerializerMethodField()
    student = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()

    def get_student(self, obj):
        student = None
        image = None
        if obj.student.profile_picture:
            image = obj.student.profile_picture.url
        if obj.student:
            request = self.context.get("request")
            student = {
                "user_id": obj.student.user_id,
                "full_name": obj.student.get_full_name(),
                "image": request.build_absolute_uri(image)
            }
        return student

    def get_subjects(self, obj):
        from home.serializers import SubjectSerializerOut
        subject = None
        if obj.subjects:
            subject = SubjectSerializerOut(obj.subjects).data
        return subject

    def get_tutor(self, obj):
        tutor = None
        image = None
        if obj.tutor.profile.profile_picture:
            image = obj.tutor.profile.profile_picture.url
        if obj.tutor:
            request = self.context.get("request")
            tutor = {
                "user_id": obj.tutor_id,
                "full_name": obj.tutor.get_full_name(),
                "image": request.build_absolute_uri(image)
            }
        return tutor

    class Meta:
        model = Classroom
        exclude = []


class CreateClassSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # Logged in student
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)
    tutor_id = serializers.IntegerField()
    calender_id = serializers.IntegerField()
    student_id = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    subject_id = serializers.IntegerField()
    book_now = serializers.BooleanField()
    # occurrence = serializers.IntegerField(required=False)

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
        lang = validated_data.get("lang", "en")
        tutor_calender_id = validated_data.get("calender_id")
        book_now = validated_data.get("book_now", False)
        # reoccur = validated_data.get("occurrence", 1)
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
        avail = get_object_or_404(TutorCalendar, id=tutor_calender_id, status="available")
        subject = get_object_or_404(Subject, id=subject_id)
        tutor_user = tutor.user
        d_site = get_site_details()

        # Get Duration
        start_date_convert = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S%z")
        end_date_convert = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S%z")
        time_difference = end_date_convert - start_date_convert
        duration = (time_difference.days * 24 * 60) + (time_difference.seconds / 60).__round__()

        if duration < 30 or duration > 120:
            raise InvalidRequestException({"detail": translate_to_language("Duration cannot be less than 30minutes or greater than 2hours", lang)})

        # Check if duration does not exceed tutor max hour
        # if duration > tutor_user.tutordetail.max_hour_class_hour:
        #     raise InvalidRequestException({"detail": "Duration cannot be greater than tutor teaching period"})

        # Check Tutor Calendar
        week_day = (start_date_convert.weekday() + 1) % 7
        if not TutorCalendar.objects.filter(
                user=tutor_user, day_of_the_week=week_day, time_from__hour=start_date_convert.hour, status="available"
        ):
            raise InvalidRequestException({"detail": translate_to_language("Tutor is not available at the selected period", lang)})

        # Calculate Class Amount
        subject_amount = subject.amount  # coin value per subject per hour
        # class_amount = reoccur * (duration * subject_amount / 60)
        class_amount = round(duration * subject_amount / 60, 2)

        # Check Tutor availability
        if Classroom.objects.filter(start_date__gte=start_date, end_date__lte=end_date, tutor=tutor_user,
                                    status__in=["new", "accepted"]).exists():
            raise InvalidRequestException({"detail": translate_to_language("Period booked by another user, please select another period", lang)})

        # Check if call occurred earlier. If yes, then add tutor rest period to start time

        if not book_now:
            return {
                "detail": "Classroom estimation complete",
                "data": {"student_name": str(user.get_full_name()).upper(), "level": subject.grade,
                         "subject": subject.name, "start_at": start_date, "end_at": end_date,
                         # "duration": f"{duration} minutes", "total_coin": class_amount, "occurrence": reoccur}
                         "duration": f"{duration} minutes", "total_coin": class_amount}
            }

        # Check parent balance is available for class amount
        balance = student.parent.user.wallet.balance
        if class_amount > balance:
            raise InvalidRequestException({"detail": translate_to_language("Insufficient balance, please top-up wallet", lang)})

        # Create class for student
        # Add grace period
        single_class_amount = class_amount
        new_end_time = end_date_convert + timezone.timedelta(minutes=int(d_site.class_grace_period))
        classroom = Classroom.objects.create(
            name=name, description=description, tutor=tutor_user, student=student, start_date=start_date,
            end_date=new_end_time, amount=single_class_amount, subjects=subject, expected_duration=duration
        )
        avail.status = "not_available"
        avail.classroom.add(classroom)
        avail.save()
        # Notify Tutor of created class
        Thread(target=tutor_class_creation_email, args=[classroom, lang]).start()
        # Notify Parent of created class
        Thread(target=parent_class_creation_email, args=[classroom, lang]).start()
        if parent_profile:
            Thread(target=create_notification,
                   args=[parent_profile.user, translate_to_language(f"New class created for student {student.user.get_full_name()}", lang)]).start()
        Thread(target=create_notification,
               args=[tutor_user, translate_to_language(f"You have a new class request from {student.user.get_full_name()}", lang)]).start()

        # initial_start_date = classroom.start_date
        # while reoccur > 1:
        #     loop_start_date = initial_start_date + timezone.timedelta(days=7)
        #     class_end_date = loop_start_date + timezone.timedelta(minutes=duration)
        #     loop_end_date = class_end_date + timezone.timedelta(minutes=int(d_site.class_grace_period))
        #     # Create Classroom
        #     loop_classroom = Classroom.objects.create(
        #         name=name, description=description, tutor=tutor_user, student=student, start_date=loop_end_date,
        #         end_date=loop_end_date, amount=single_class_amount, subjects=subject, expected_duration=duration
        #     )
        #     avail.classroom.add(loop_classroom)
        #     initial_start_date = loop_classroom.start_date
        #     reoccur -= 1

        return {
            "detail": translate_to_language("Classroom request sent successfully", lang),
            "data": ClassRoomSerializerOut(classroom, context={"request": self.context.get("request")}).data
        }


class ApproveDeclineClassroomSerializerIn(serializers.Serializer):
    action = serializers.ChoiceField(choices=ACCEPT_DECLINE_STATUS)
    decline_reason = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        action = validated_data.get("action")
        decline_reason = validated_data.get("decline_reason")
        lang = validated_data.get("lang", "en")
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
            student_email = parent.email
            response = ZoomAPI.create_meeting(
                start_date=str(instance.start_date), duration=instance.expected_duration,
                attending=[{"name": str(student_name), "email": str(student_email)},
                           {"name": str(tutor_name), "email": str(tutor_email)}], narration=instance.description,
                title=instance.name
            )
            zoom_meeting_id = response["id"]
            link = response["join_url"]
            instance.status = "accepted"
            instance.meeting_link = link
            instance.meeting_id = zoom_meeting_id
            # Debit parent wallet
            parent_wallet.refresh_from_db()
            parent_wallet.balance -= amount
            parent_wallet.save()
            # Check parent new wallet balance and compare coin threshold
            parent_wallet.refresh_from_db()
            if parent_wallet.balance < d_site.coin_threshold:
                # Send low coin threshold email to parent
                Thread(target=parent_low_threshold_email, args=[parent, parent_wallet.balance, lang]).start()

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
            Thread(target=student_class_approved_email, args=[instance, lang]).start()
            # Send notification to parent
            # Send meeting link to tutor
            Thread(target=tutor_class_approved_email, args=[instance, lang]).start()
            Thread(target=create_notification,
                   args=[student, translate_to_language(f"Your class request has been approved by {tutor_name}", lang)]).start()
            Thread(target=create_notification,
                   args=[instance.tutor, translate_to_language(f"You accepted a new class request with {student_name}", lang)]).start()
        elif action == "cancel":
            # Check if instance was initially in accepted state
            if not instance.status == "accepted":
                raise InvalidRequestException({"detail": translate_to_language("You can only cancel class request you recently accepted", lang)})
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
            # Set Tutor Availability
            instance.tutorcalendar_set.all().update(status="available")
            for tutor_calendar in instance.tutorcalendar_set.all():
                tutor_calendar.classroom.clear()
            # TutorCalendar.objects.filter(classroom=instance).update(status="available")
            # Create refund transaction
            Transaction.objects.create(
                user=parent, transaction_type="refund", amount=amount, narration=f"Refund, {instance.description}",
                status="completed"
            )
            # Notify parent and student
            Thread(target=parent_class_cancel_email, args=[parent, amount, lang]).start()
            Thread(target=student_class_cancel_email, args=[student, lang]).start()
        else:
            if not decline_reason:
                raise InvalidRequestException({"detail": translate_to_language("Kindly specify reason why you are declining this request", lang)})
            # Update instance state
            instance.decline_reason = decline_reason
            instance.status = "declined"
            instance.tutorcalendar_set.all().update(status="available")
            for tutor_calendar in instance.tutorcalendar_set.all():
                tutor_calendar.classroom.clear()

            # Send notification to student
            Thread(target=student_class_declined_email, args=[instance, lang]).start()
            # Send notification to parent
        instance.save()
        return ClassRoomSerializerOut(instance, context={"request": self.context.get("request")}).data


class DisputeSerializerOut(serializers.ModelSerializer):
    submitted_by = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        image = None
        if obj.image:
            request = self.context.get("request")
            image = request.build_absolute_uri(obj.image.url)
        return image

    def get_submitted_by(self, obj):
        return {
            "user_id": obj.submitted_by_id,
            "full_name": obj.submitted_by.get_full_name()
        }

    class Meta:
        model = Dispute
        exclude = []


class DisputeSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    title = serializers.CharField(max_length=200, required=False)
    dispute_type = serializers.ChoiceField(choices=DISPUTE_TYPE_CHOICES)
    image = serializers.ImageField(required=False)
    content = serializers.CharField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        title = validated_data.get("title")
        d_type = validated_data.get("dispute_type")
        content = validated_data.get("content")
        image = validated_data.get("image")
        lang = validated_data.get("lang", "en")

        if not title:
            raise InvalidRequestException({"detail": translate_to_language("Title is required", lang)})

        # Create Dispute
        dispute, _ = Dispute.objects.get_or_create(submitted_by=user, title=title)
        dispute.dispute_type = d_type
        dispute.image = image
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
    # classroom = serializers.SerializerMethodField()

    # def get_classroom(self, obj):
    #     classroom = None
    #     if obj.classroom:
    #         classroom = dict()
    #         classroom["id"] = obj.classroom_id
    #         classroom["student_name"] = obj.classroom.student.get_full_name()
    #         classroom["status"] = obj.classroom.status
    #         classroom["class_type"] = obj.classroom.class_type
    #         classroom["name"] = obj.classroom.name
    #     return classroom

    class Meta:
        model = TutorCalendar
        exclude = []


class TutorCalendarSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    data = serializers.ListSerializer(child=serializers.DictField())
    lang = serializers.CharField(required=False)
    # week_day = serializers.ChoiceField(choices=DAY_OF_THE_WEEK_CHOICES)
    # start_time = serializers.TimeField()
    # end_time = serializers.TimeField()
    # status = serializers.ChoiceField(choices=AVAILABILITY_STATUS_CHOICES)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        data_list = validated_data.get("data")
        lang = validated_data.get("lang", "en")

        # Delete all user's availability
        # if TutorCalendar.objects.filter(status="not_available").exists():
        #     raise InvalidRequestException({"detail": "There are existing/open classes. Please close or complete them"})
        TutorCalendar.objects.filter(user=user).delete()

        # Create availability
        try:
            for item in data_list:
                week_day = item.get("week_day")
                start_period = item.get("start_time")
                end_period = item.get("end_time")
                avail_status = item.get("status")
                TutorCalendar.objects.create(
                    user=user, day_of_the_week=week_day, time_from=start_period, time_to=end_period, status=avail_status
                )
        except Exception as err:
            log_request(f"Error while adding calendar: {err}")

        # Check if time within a day already exists
        # if TutorCalendar.objects.filter(user=user, day_of_the_week=week_day).exclude(
        #         Q(time_from__gte=end_period) | Q(time_to__lte=start_period)).exists():
        #     Get the schedule and update
            # avail = TutorCalendar.objects.filter(user=user, day_of_the_week=week_day).exclude(
            #     Q(time_from__gte=end_period) | Q(time_to__lte=start_period)).last()
            # avail.time_from = start_period
            # avail.time_to = end_period
            # avail.status = avail_status
            # avail.save()
            # return TutorCalendarSerializerOut(avail, context={"request": self.context.get("request")}).data
            #
            # raise InvalidRequestException({"detail": "Overlapping time frame"})
        #
        # avail, _ = TutorCalendar.objects.get_or_create(user=user, day_of_the_week=week_day, time_from=start_period)
        # avail.time_to = end_period
        # avail.status = avail_status
        # avail.save()

        # return TutorCalendarSerializerOut(avail, context={"request": self.context.get("request")}).data
        return {"detail": translate_to_language("Calendar updated", lang)}


class TutorBankAccountSerializerOut(serializers.ModelSerializer):
    routing_number = serializers.SerializerMethodField()

    def get_routing_number(self, obj):
        if obj.routing_number:
            return mask_number(obj.routing_number, 5)
        return None

    class Meta:
        model = TutorBankAccount
        exclude = []


class TutorBankAccountSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    bank_name = serializers.CharField()
    lang = serializers.CharField(required=False)
    # routing_number = serializers.CharField(required=False)
    routing_number = serializers.CharField(required=False)
    # country_id = serializers.IntegerField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        bank = validated_data.get("bank_name")
        # routing_no = validated_data.get("routing_number")
        # country_id = validated_data.get("country_id")
        lang = validated_data.get("lang", "en")

        country = get_object_or_404(Country, alpha2code__iexact="fr")
        tutor = get_object_or_404(Profile, user=user, account_type="tutor")
        if not tutor.stripe_verified and tutor.stripe_connect_account_id:
            raise InvalidRequestException(
                {"success": False, "detail": translate_to_language(
                    "You need to complete your Stripe Connect onboarding process to continue", lang)}
            )

        try:

            stripe_connected_acct = tutor.stripe_connect_account_id
            acct_no = ""

            # Add Bank Details to Connected Stripe Account
            external_account = StripeAPI.create_external_account(
                acct=stripe_connected_acct, account_no=acct_no, country_code=str(country.alpha2code).upper(),
                currency_code=str(country.currency_code).lower()
            )
            external_account_id = external_account.get("id")
            if external_account_id:
                acct, _ = TutorBankAccount.objects.get_or_create(user=user, bank_name=bank)
                acct.country = country
                acct.stripe_external_account_id = external_account_id
                acct.save()

                return {
                    "success": True,
                    "detail": TutorBankAccountSerializerOut(acct, context={"request": self.context.get("request")}).data
                }
            raise InvalidRequestException(
                {"success": False,
                 "detail": translate_to_language("Could not validate account number, please try again later", lang)}
            )
        except Exception as err:
            log_request(f"Error while adding external bank account:\n{err}")
            raise InvalidRequestException(
                {"success": False,
                 "detail": translate_to_language("An error has occurred, please try again later", lang)}
            )


class PayoutSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = PayoutRequest
        exclude = []


class RequestPayoutSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # amount = serializers.FloatField()
    bank_account_id = serializers.IntegerField()
    request_now = serializers.BooleanField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        # coin = validated_data.get("amount")
        bank_acct_id = validated_data.get("bank_account_id")
        lang = validated_data.get("lang", "en")
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
                "detail": translate_to_language("Payout estimation complete", lang),
                "data": {"name": str(user.get_full_name()).upper(), "wallet_balance": user_wallet.balance,
                         "coin_to_withdraw": coin, "amount_equivalent": f"EUR{amount}"}
            }
        # Create Payout Request
        if amount < 1:
            raise InvalidRequestException({"detail": translate_to_language("Amount too low. Minimum payout amount is One Euro", lang)})
        payout = PayoutRequest.objects.create(user=user, bank_account=bank_acct, coin=coin, amount=amount)

        # Subtract payout coin from balance
        balance = StripeAPI.get_account_balance()
        new_balance = float(balance / 100)
        stripe_connect_account_id = user.profile.stripe_connect_account_id

        if amount > new_balance:
            log_request({"detail": f"Payout for {user.get_full_name()} failed due to low Stripe Balance"})
            # Send low balance email to admin
            raise InvalidRequestException({"detail": translate_to_language("Cannot process the withdrawal, please try again later", lang)})

        narration = f"EduDream Payout of EUR{amount} to {user.get_full_name()}"

        # Process Transfer
        response = StripeAPI.transfer_to_connect_account(amount=amount, acct=stripe_connect_account_id, desc=narration)
        transfer_trx_ref = response.get("id")
        user_wallet.refresh_from_db()
        # Subtract Coin
        user_wallet.balance -= coin
        user_wallet.save()

        # Create Transaction
        trans = Transaction.objects.create(
            user=user, transaction_type="withdrawal", amount=amount, narration=narration, reference=transfer_trx_ref
        )
        payout.transaction = trans
        payout.save()

        # Send Email to user
        Thread(target=payout_request_email, args=[user, lang]).start()
        return {"detail": translate_to_language("Success", lang),
                "data": PayoutSerializerOut(payout, context={"request": self.context.get("request")}).data}


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
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        tutor_id = validated_data.get("tutor_id")
        student_id = validated_data.get("student_id")
        lang = validated_data.get("lang", "en")
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
            raise InvalidRequestException({"detail": translate_to_language("Tutor is not accepting intro call at the moment", lang)})

        tutor_user = tutor.user
        d_site = get_site_details()

        # Calculate Call End Period
        call_duration = int(d_site.intro_call_duration)
        start_date_convert = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S%z")
        end_date = start_date_convert + datetime.timedelta(minutes=call_duration)
        # Check Tutor Calendar
        # if not TutorCalendar.objects.filter(
        #         user=tutor_user, day_of_the_week=start_date_convert.isoweekday(),
        #         time_from__hour=start_date_convert.hour, status="available"
        # ):
        #     raise InvalidRequestException({"detail": "Tutor is not available at the selected period"})

        # Check Tutor availability
        if Classroom.objects.filter(start_date__gte=start_date, end_date__lte=end_date, tutor=tutor_user,
                                    status__in=["new", "accepted"]).exists():
            raise InvalidRequestException({"detail": translate_to_language("Period booked by another user, please select another period", lang)})

        tutor_email = tutor_user.email
        tutor_name = str("{} {}").format(tutor_user.first_name, tutor_user.last_name).upper()
        sender_email = student.parent.user.email
        sender_name = student.user.get_full_name()
        if parent_profile:
            sender_email = parent_profile.email()
            sender_name = parent_profile.get_full_name()
        response = ZoomAPI.create_meeting(
            start_date=str(start_date_convert), duration=call_duration,
            attending=[{"name": str(sender_name), "email": str(sender_email)},
                       {"name": str(tutor_name), "email": str(tutor_email)}], narration=f"Intro call {tutor_name}",
            title=f"Intro call with {tutor_name}"
        )
        link = response["join_url"]
        # Send invitation link to tutor, parent and/or student and create in-app notification
        if link is not None:
            Thread(target=parent_intro_call_email, args=[user, tutor_name, start_date, end_date, link, lang]).start()
            Thread(target=tutor_intro_call_email,
                   args=[tutor_user, user.get_full_name(), start_date, end_date, link, lang]).start()
            Thread(target=create_notification, args=[user, translate_to_language(f"Intro call scheduled with {tutor_name}", lang)]).start()
            Thread(target=create_notification, args=[user, translate_to_language(f"New Intro call request from {sender_name}", lang)]).start()

        return translate_to_language("Intro call booked successfully. Detail will be sent to your email address", lang)
    # except Exception as err:
    #     log_request(f"Error while booking intro call\nError: {err}")
    #     raise InvalidRequestException({"detail": "Cannot process request at the moment. Please try again later"})


class CustomClassSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # Logged in tutor
    name = serializers.CharField()
    note = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)
    student_id = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    subject_id = serializers.IntegerField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        name = validated_data.get("name")
        description = validated_data.get("note")
        student_id = validated_data.get("student_id")
        start_date = str(validated_data.get("start_date"))
        end_date = str(validated_data.get("end_date"))
        subject_id = validated_data.get("subject_id")
        lang = validated_data.get("lang", "en")

        student = get_object_or_404(Student, user_id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        d_site = get_site_details()

        # Get Duration
        start_date_convert = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S%z")
        end_date_convert = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S%z")
        time_difference = end_date_convert - start_date_convert
        duration = (time_difference.days * 24 * 60) + (time_difference.seconds / 60).__round__()

        # Calculate Class Amount
        subject_amount = subject.amount  # coin value per subject per hour
        class_amount = duration * subject_amount / 60

        # Add grace period
        new_end_time = end_date_convert + timezone.timedelta(minutes=int(d_site.class_grace_period))

        # Create class for student
        classroom = Classroom.objects.create(
            name=name, description=description, tutor=user, student=student, start_date=start_date,
            end_date=new_end_time, amount=class_amount, subjects=subject, expected_duration=duration, status="new",
            class_type="custom"
        )

        # Create ChatMessage for CustomClass
        # ChatMessage.objects.create(sender=sender, receiver_id=receiver, message=message, attachment=upload)
        chat_message = f"<p>Hi {student.user.get_full_name()}, &nbsp;I have just created a custom classroom.</p>" \
                       f"<p>Please see details below:</p><p>Start Date: {start_date}</p><p>End Date: {end_date}</p>" \
                       f"<p>You can accept or reject this request from your classrooms on dashboard</p>"
        ChatMessage.objects.create(sender=user, receiver=student.user, message=translate_to_language(chat_message, lang))

        # Send meeting link to student
        # Thread(target=student_class_approved_email, args=[instance]).start()
        # Send notification to parent
        # Send meeting link to tutor
        # Thread(target=tutor_class_approved_email, args=[instance]).start()
        # Thread(target=create_notification, args=[student, f"Your class request has been approved by {tutor_name}"]).start()
        # Thread(target=create_notification, args=[instance.tutor, f"You accepted a new class request with {student_name}"]).start()

        return ClassRoomSerializerOut(classroom, context={"request": self.context.get("request")}).data

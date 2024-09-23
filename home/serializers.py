import decimal
import uuid
from threading import Thread

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from edudream.modules.choices import ACCOUNT_TYPE_CHOICES, CONSULTATION_ACCOUNT_TYPE, CONSULTATION_TYPE_CHOICES
from edudream.modules.email_template import tutor_register_email, parent_register_email, feedback_email, \
    consultation_email, send_otp_token_to_email, send_verification_email, send_welcome_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.utils import generate_random_otp, log_request, encrypt_text, get_next_minute, \
    decrypt_text, create_notification, translate_to_language, get_site_details, get_current_datetime_from_lat_lon
from home.models import Profile, Wallet, Transaction, ChatMessage, PaymentPlan, ClassReview, Language, UserLanguage, \
    Subject, Notification, Testimonial
from location.models import Country, State, City
from parent.serializers import ParentStudentSerializerOut
from student.models import Student
from tutor.models import TutorDetail, Classroom, Dispute
from tutor.serializers import TutorDetailSerializerOut, ClassRoomSerializerOut


class UserLanguageSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = UserLanguage
        exclude = ["user"]


class TutorListSerializerOut(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id")
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.CharField(source="user.email")
    tutor_languages = serializers.SerializerMethodField()
    detail = serializers.SerializerMethodField()
    wallet = serializers.SerializerMethodField()
    can_start_conversation = serializers.SerializerMethodField()

    def get_can_start_conversation(self, obj):
        can_start_conversation = False
        request = self.context.get("request")
        auth_user = request.user
        if auth_user is not None:
            users = [auth_user.id, obj.user.id]
            query = Q(tutor_id__in=users) | Q(student__user_id__in=users) | Q(student__parent__user_id__in=users)
            if Classroom.objects.filter(query).exists():
                can_start_conversation = True
        return can_start_conversation

    def get_tutor_languages(self, obj):
        if UserLanguage.objects.filter(user__profile=obj).exists():
            return UserLanguageSerializerOut(UserLanguage.objects.filter(user__profile=obj), many=True).data
        return None

    def get_detail(self, obj):
        return TutorDetailSerializerOut(TutorDetail.objects.get(user__profile=obj), context={"request": self.context.get("request")}).data

    def get_wallet(self, obj):
        wallet = Wallet.objects.filter(user=obj.user).last()
        return {"id": wallet.id, "balance": wallet.balance, "approximate_hours": round(float(wallet.balance) / 7.5)}

    class Meta:
        model = Profile
        exclude = ["user", "dob", "address", "city", "state", "stripe_customer_id", "referred_by", "referral_code"]


class ProfileSerializerOut(serializers.ModelSerializer):
    wallet = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    full_name = serializers.CharField(source="user.get_full_name")

    def get_profile_picture(self, obj):
        request = self.context.get("request")
        if obj.profile_picture:
            return request.build_absolute_uri(obj.profile_picture.url)
        return None

    def get_children(self, obj):
        if Student.objects.filter(parent=obj, parent__account_type="parent").exists():
            return ParentStudentSerializerOut(Student.objects.filter(parent=obj, parent__account_type="parent"), many=True).data
        return None

    def get_wallet(self, obj):
        wallet = Wallet.objects.filter(user=obj.user).last()
        payout_ratio = get_site_details().payout_coin_to_amount
        wallet_amount = decimal.Decimal(wallet.balance) * payout_ratio

        return {"id": wallet.id, "balance": wallet.balance, "wallet_amount": wallet_amount, "expected_balance": wallet.pending, "approximate_hours": round(float(wallet.balance) / 7.5)}

    class Meta:
        model = Profile
        exclude = ["dob", "address", "city", "state", "email_verified_code", "stripe_customer_id", "stripe_connect_account_id"]


class UserSerializerOut(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    is_tutor = serializers.SerializerMethodField()
    is_student = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    stat = serializers.SerializerMethodField()
    timezone_data = serializers.SerializerMethodField()

    def get_timezone_data(self, obj):
        if Profile.objects.filter(user=obj).exists():
            user_profile = Profile.objects.get(user=obj)
            tzone, ctime, utc_offset = get_current_datetime_from_lat_lon(float(user_profile.lat), float(user_profile.lon))
            return {"timezone": tzone, "current_time": ctime, "utc_offset": utc_offset}
        return None

    def get_stat(self, obj):
        if Student.objects.filter(user=obj).exists():
            student = Student.objects.get(user=obj)
            classroom = Classroom.objects.filter(student__user=obj)
            tutors = [classes.tutor_id for classes in classroom]
            tutor_list = list(dict.fromkeys(tutors))
            now = timezone.now()
            ended_class = classroom.filter(end_date__lte=now, student_complete_check=False, status="accepted")
            ap = classroom.filter(end_date__lte=now, tutor_complete_check=False, status="accepted")
            return {
                "total_tutor": len(tutor_list),
                "total_subject": Subject.objects.filter(classroom__student=student).distinct().count(),
                "active_classes": classroom.filter(status="accepted").count(),
                "completed_classes": classroom.filter(status="completed").count(),
                "ended_classes": ClassRoomSerializerOut(ended_class, many=True, context={"request": self.context.get("request")}).data,
                "awaiting_approval": ClassRoomSerializerOut(ap, many=True, context={"request": self.context.get("request")}).data,
            }
        elif Profile.objects.filter(user=obj, account_type="parent").exists():
            classroom = Classroom.objects.filter(student__parent__user=obj)
            tutors = [classes.tutor_id for classes in classroom]
            tutor_list = list(dict.fromkeys(tutors))
            students = Student.objects.filter(parent__user=obj)
            now = timezone.now()
            ended_class = classroom.filter(end_date__lte=now, student_complete_check=False, status="accepted")
            ap = classroom.filter(end_date__lte=now, tutor_complete_check=False, status="accepted")
            return {
                "total_tutor": len(tutor_list),
                "total_subject": Subject.objects.filter(classroom__student__in=students).distinct().count(),
                "total_student": students.count(),
                "active_classes": classroom.filter(status="accepted").count(),
                "completed_classes": classroom.filter(status="completed").count(),
                "ended_classes": ClassRoomSerializerOut(ended_class, many=True, context={"request": self.context.get("request")}).data,
                "awaiting_approval": ClassRoomSerializerOut(ap, many=True, context={"request": self.context.get("request")}).data,
            }
        elif Profile.objects.filter(user=obj, account_type="tutor").exists():
            classroom = Classroom.objects.filter(tutor=obj)
            now = timezone.now()
            ended_class = classroom.filter(end_date__lte=now, tutor_complete_check=False, status="accepted")
            ap = classroom.filter(end_date__lte=now, student_complete_check=False, status="accepted")
            return {
                "total_subject": Subject.objects.filter(classroom__tutor__in=[obj]).distinct().count(),
                "active_classes": classroom.filter(status="accepted").count(),
                "completed_classes": classroom.filter(status="completed").count(),
                "cancelled_classes": classroom.filter(status="cancelled").count(),
                "ended_classes": ClassRoomSerializerOut(ended_class, many=True, context={"request": self.context.get("request")}).data,
                "awaiting_approval": ClassRoomSerializerOut(ap, many=True, context={"request": self.context.get("request")}).data,
            }

        else:
            return None

    def get_languages(self, obj):
        return UserLanguageSerializerOut(UserLanguage.objects.filter(user=obj), many=True).data

    def get_user_detail(self, obj):
        try:
            return ProfileSerializerOut(Profile.objects.get(user=obj), context={"request": self.context.get("request")}).data
        except Profile.DoesNotExist:
            return {"account_type": "student"}

    def get_is_student(self, obj):
        if Student.objects.filter(user=obj).exists():
            request = self.context.get("request")
            student = Student.objects.get(user=obj)
            parent = student.parent
            profile_picture = None
            if student.profile_picture:
                profile_picture = request.build_absolute_uri(student.profile_picture.url)

            return {
                # "dob": student.dob,
                "user_id": student.user_id,
                "grade": student.grade,
                # "address": parent.address,
                # "city_id": parent.city_id,
                # "state_id": parent.state_id,
                "country_id": parent.country_id,
                "profile_picture": profile_picture,
                # "city_name": parent.city.name,
                # "state_name": parent.state.name,
                "country_name": parent.country.name,
                # "full_address": parent.get_full_address(),
                "parent_name": parent.get_full_name(),
                "parent_email": parent.email(),
                "parent_mobile": parent.mobile_number,
                "parent_wallet_balance": parent.user.wallet.balance
            }
        return False

    def get_is_tutor(self, obj):
        try:
            return TutorDetailSerializerOut(TutorDetail.objects.get(user=obj), context={"request": self.context.get("request")}).data
        except TutorDetail.DoesNotExist:
            return False

    class Meta:
        model = User
        exclude = ["is_staff", "is_active", "is_superuser", "password", "groups", "user_permissions"]


class SignUpSerializerIn(serializers.Serializer):
    lang = serializers.CharField(required=False)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email_address = serializers.EmailField()
    password = serializers.CharField()
    address = serializers.CharField(max_length=300, required=False)
    account_type = serializers.ChoiceField(choices=ACCOUNT_TYPE_CHOICES)
    mobile_number = serializers.CharField(max_length=20)
    # dob = serializers.DateTimeField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.IntegerField(required=False)
    country = serializers.IntegerField()
    postal_code = serializers.CharField(required=False)
    address_front_file = serializers.FileField(required=False)
    address_back_file = serializers.FileField(required=False)
    nationality_front_file = serializers.FileField(required=False)
    nationality_back_file = serializers.FileField(required=False)

    languages = serializers.CharField(required=False)
    bio = serializers.CharField(required=False)
    hobbies = serializers.CharField(required=False)
    funfact = serializers.CharField(required=False)
    linkedin = serializers.CharField(required=False)
    education_status = serializers.CharField(required=False)
    university_name = serializers.CharField(required=False)
    high_school_attended = serializers.CharField(required=False)
    high_school_subject = serializers.CharField(required=False)
    discipline = serializers.CharField(required=False)
    diploma_type = serializers.CharField(required=False)
    diploma_grade = serializers.CharField(required=False)
    diploma_file = serializers.FileField(required=False)
    resume = serializers.FileField(required=False)
    proficiency_test_file = serializers.FileField(required=False)
    proficiency_test_grade = serializers.CharField(required=False)
    proficiency_test_type = serializers.CharField(required=False)
    rest_period = serializers.IntegerField(required=False)
    referral_code = serializers.CharField(required=False)
    subject = serializers.ListSerializer(required=False, child=serializers.IntegerField())

    def create(self, validated_data):
        lang = validated_data.get("lang", "en")
        f_name = validated_data.get("first_name")
        l_name = validated_data.get("last_name")
        email = validated_data.get("email_address")
        password = validated_data.get("password")
        acct_type = validated_data.get("account_type")
        address = validated_data.get("address")
        phone_number = validated_data.get("mobile_number")
        # d_o_b = validated_data.get("dob")
        city = validated_data.get("city")
        postal_code = validated_data.get("postal_code")
        address_front = validated_data.get("address_front_file", None)
        address_back = validated_data.get("address_back_file", None)
        nationality_front = validated_data.get("nationality_front_file", None)
        nationality_back = validated_data.get("nationality_back_file", None)

        state_id = validated_data.get("state")
        country_id = validated_data.get("country")
        languages = validated_data.get("languages")
        bio = validated_data.get("bio")
        hobbies = validated_data.get("hobbies")
        funfact = validated_data.get("funfact")
        linkedin = validated_data.get("linkedin", "http")
        education_status = validated_data.get("education_status")
        university_name = validated_data.get("university_name")
        high_school_attended = validated_data.get("high_school_attended")
        high_school_subject = validated_data.get("high_school_subject")
        discipline = validated_data.get("discipline")
        diploma_type = validated_data.get("diploma_type")
        diploma_file = validated_data.get("diploma_file")
        diploma_grade = validated_data.get("diploma_grade")
        proficiency_test_file = validated_data.get("proficiency_test_file")
        proficiency_test_grade = validated_data.get("proficiency_test_grade")
        proficiency_test_type = validated_data.get("proficiency_test_type")
        rest_period = validated_data.get("rest_period", 10)
        referral_code = validated_data.get("referral_code")
        subjects = validated_data.get("subject")
        resume_file = validated_data.get("resume")

        required_for_tutor = [
            bio, hobbies, funfact, education_status, diploma_type, diploma_file, proficiency_test_file, diploma_grade,
            languages, proficiency_test_grade, resume_file, high_school_subject, high_school_attended, country_id,
            # state_id, address, city_id, postal_code, address_front, address_back, nationality_front
            # nationality_back
        ]
        if acct_type == "tutor" and not all(required_for_tutor):
            raise InvalidRequestException({"detail": translate_to_language("Please submit all required details", lang)})
        country = get_object_or_404(Country, id=country_id)

        if User.objects.filter(username__iexact=email).exists():
            raise InvalidRequestException({"detail": translate_to_language("Email is taken", lang)})

        if User.objects.filter(email__iexact=email).exists():
            raise InvalidRequestException({"detail": translate_to_language("Email is taken", lang)})

        try:
            validate_password(password=password)
        except Exception as err:
            raise InvalidRequestException({'detail': translate_to_language(', '.join(list(err)), lang)})

        # if password != password_confirm:
        #     raise InvalidRequestException({'detail': 'Passwords mismatch'})

        email_token = generate_random_otp()
        log_request(f"Email Token for email - {email}: {email_token}")

        referrer = None
        if referral_code:
            try:
                referrer_profile = Profile.objects.get(referral_code=referral_code)
                referrer = referrer_profile.user
            except Profile.DoesNotExist:
                pass

        user, _ = User.objects.get_or_create(username=email)
        user.email = email
        user.first_name = f_name
        user.last_name = l_name
        user.set_password(raw_password=password)
        user.save()

        if not str(linkedin).startswith("http"):
            linkedin = f"https://{linkedin}"

        if languages:
            for language in eval(languages):
                language_id = language["language_id"]
                language_proficiency = language["proficiency"]

                try:
                    lang, _ = UserLanguage.objects.get_or_create(user=user, language_id=language_id)
                    lang.proficiency = language_proficiency
                    lang.save()
                except Exception as err:
                    log_request(f"Error on User Language Creation: {err}")
                    pass

        profile, _ = Profile.objects.get_or_create(user=user)
        # if d_o_b:
        #     profile.dob = d_o_b
        profile.country = country
        # profile.state = state
        # profile.city = city
        profile.mobile_number = phone_number
        # profile.address = address
        profile.account_type = acct_type
        profile.email_verified_code = encrypt_text(email_token)
        profile.code_expiry = get_next_minute(timezone.now(), 15)
        profile.referral_code = str(uuid.uuid4()).replace("-", "")[:8]
        profile.referred_by = referrer
        profile.active = True
        profile.save()

        # Create Wallet
        Wallet.objects.get_or_create(user=user)

        # Create TutorDetail if account type is "tutor"
        if acct_type == "tutor":
            # state = get_object_or_404(State, id=state_id, country_id=country_id)
            # city = get_object_or_404(City, id=city_id, state_id=state_id)

            Profile.objects.filter(user=user).update(
                active=False
                # active=False, city=city, address=address, state=state, postal_code=postal_code
            )
            tutor_detail, _ = TutorDetail.objects.get_or_create(user=user)
            tutor_detail.bio = bio
            tutor_detail.hobbies = hobbies
            tutor_detail.funfact = funfact
            tutor_detail.linkedin = linkedin
            tutor_detail.education_status = education_status
            tutor_detail.university_name = university_name
            tutor_detail.high_school_attended = high_school_attended
            tutor_detail.high_school_subject = high_school_subject
            tutor_detail.discipline = discipline
            tutor_detail.diploma_type = diploma_type
            tutor_detail.diploma_file = diploma_file
            tutor_detail.diploma_grade = diploma_grade
            tutor_detail.proficiency_test_grade = proficiency_test_grade
            tutor_detail.proficiency_test_file = proficiency_test_file
            tutor_detail.address_front_file = address_front
            tutor_detail.address_back_file = address_back
            tutor_detail.nationality_front_file = nationality_front
            tutor_detail.nationality_back_file = nationality_back
            tutor_detail.proficiency_test_type = proficiency_test_type
            tutor_detail.resume = resume_file
            tutor_detail.rest_period = rest_period
            if subjects:
                tutor_detail.subjects.clear()
                for subject in subjects:
                    tutor_detail.subjects.add(subject)

            tutor_detail.save()
            # Send Register Email to Tutor
            Thread(target=tutor_register_email, args=[user, lang]).start()
        else:
            # Send Register Email to Parent
            Thread(target=parent_register_email, args=[user, lang]).start()
        # Send Verification token to email

        Thread(target=create_notification, args=[user, translate_to_language("Welcome to EduDream", lang)]).start()
        return UserSerializerOut(user, context={"request": self.context.get("request")}).data


class LoginSerializerIn(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        username = validated_data.get("username")
        password = validated_data.get("password")
        lang = validated_data.get("lang", "en")

        user = authenticate(username=username, password=password)
        if not user:
            # raise InvalidRequestException({"detail": "Invalid email/username or password"})
            raise InvalidRequestException({"detail": translate_to_language("Invalid email/username or password", lang)})

        if Student.objects.filter(user=user).exists():
            student = Student.objects.get(user=user)
            if student.parent.email_verified is False:
                raise InvalidRequestException(
                    {"detail": translate_to_language("Parent email is not verified. Please ask parent/guadian to verify their account", lang)}
                )
            return user

        user_profile = Profile.objects.get(user=user)
        if user_profile.account_type == "tutor" and user_profile.active is False:
            raise InvalidRequestException(
                {"detail": translate_to_language("Your tutor account is yet to be approved by the admin, please check back later", lang)}
            )

        if not user_profile.email_verified:
            user_profile.email_verified_code = uuid.uuid1()
            user_profile.code_expiry = get_next_minute(timezone.now(), 15)
            user_profile.save()

            # Send OTP to user
            Thread(target=send_verification_email, args=[user_profile, lang]).start()
            raise InvalidRequestException({
                "detail": translate_to_language("Kindly verify account to continue. Check email for verification link", lang)
            })
        return user


class EmailVerificationSerializerIn(serializers.Serializer):
    token = serializers.CharField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        token = validated_data.get("token")
        lang = validated_data.get("lang", "en")
        if not Profile.objects.filter(email_verified_code=token).exists():
            raise InvalidRequestException({"detail": translate_to_language("Invalid Verification code", lang)})

        user_profile = Profile.objects.get(email_verified_code=token)
        if timezone.now() > user_profile.code_expiry:
            raise InvalidRequestException({"detail": translate_to_language("Verification code has expired", lang)})

        user_profile.email_verified = True
        user_profile.email_verified_code = ""
        user_profile.save()

        # Send Email to user
        Thread(target=send_welcome_email, args=[user_profile, lang]).start()
        return translate_to_language("Your email is successfully verified, please proceed to login", lang)


class RequestVerificationLinkSerializerIn(serializers.Serializer):
    email = serializers.EmailField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        email = validated_data.get("email")
        lang = validated_data.get("lang", "en")
        try:
            user_profile = Profile.objects.get(user__email=email)
        except Profile.DoesNotExist:
            raise InvalidRequestException({"detail": translate_to_language("User with this email is not found", lang)})

        if user_profile.email_verified:
            raise InvalidRequestException({"detail": translate_to_language("Account is already verified, please proceed to login", lang)})

        user_profile.email_verified_code = uuid.uuid1()
        user_profile.code_expiry = get_next_minute(timezone.now(), 15)
        user_profile.save()

        # Send email verification link to user
        Thread(target=send_verification_email, args=[user_profile, lang]).start()
        return translate_to_language("Verfication link sent to your email", lang)


class ProfileSerializerIn(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    address = serializers.CharField(max_length=300, required=False)
    mobile_number = serializers.CharField(max_length=20, required=False)
    diploma_file = serializers.FileField(required=False)
    proficiency_test_file = serializers.FileField(required=False)

    postal_code = serializers.CharField(required=False)
    address_front_file = serializers.FileField(required=False)
    address_back_file = serializers.FileField(required=False)
    nationality_front_file = serializers.FileField(required=False)
    nationality_back_file = serializers.FileField(required=False)

    first_name = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    dob = serializers.DateTimeField(required=False)
    city = serializers.IntegerField(required=False)
    state = serializers.IntegerField(required=False)
    country = serializers.IntegerField(required=False)
    bio = serializers.CharField(required=False)
    languages = serializers.CharField(required=False)
    max_student = serializers.IntegerField(required=False)
    subject = serializers.ListSerializer(required=False, child=serializers.IntegerField())
    allow_intro_call = serializers.BooleanField(required=False)
    max_hour_class_hour = serializers.IntegerField(required=False)

    high_school_attended = serializers.CharField(required=False)
    high_school_subject = serializers.CharField(required=False)
    diploma_type = serializers.CharField(required=False)
    proficiency_test_type = serializers.CharField(required=False)
    university_name = serializers.CharField(required=False)
    education_status = serializers.CharField(required=False)
    discipline = serializers.CharField(required=False)
    diploma_grade = serializers.CharField(required=False)
    proficiency_test_grade = serializers.CharField(required=False)
    hobbies = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    funfact = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    linkedin = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    longitude = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    latitude = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def update(self, instance, validated_data):
        user = validated_data.get("user")
        lang = validated_data.get("lang", "en")
        country_id = validated_data.get("country")
        state_id = validated_data.get("state")
        city = validated_data.get("city")
        subjects = validated_data.get("subject")
        languages = validated_data.get("languages")
        diploma_file = validated_data.get("diploma_file")
        proficiency_test_file = validated_data.get("proficiency_test_file")
        address_front_file = validated_data.get("address_front_file")
        address_back_file = validated_data.get("address_back_file")
        nationality_front_file = validated_data.get("nationality_front_file")
        nationality_back_file = validated_data.get("nationality_back_file")

        instance.address = validated_data.get('address', instance.address)
        instance.postal_code = validated_data.get('postal_code', instance.postal_code)
        instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.city = validated_data.get('city', instance.city)
        instance.lon = validated_data.get('longitude', instance.lon)
        instance.lat = validated_data.get('latitude', instance.lat)
        user.first_name = validated_data.get('first_name', user.first_name)
        user.last_name = validated_data.get('last_name', user.last_name)
        if country_id:
            country = get_object_or_404(Country, id=country_id)
            instance.country = country
        if state_id:
            state = get_object_or_404(State, id=state_id)
            instance.state = state

        if instance.account_type == "tutor":
            tutor_detail = TutorDetail.objects.filter(user=user).last()
            tutor_detail.high_school_attended = validated_data.get("high_school_attended", tutor_detail.high_school_attended)
            tutor_detail.high_school_subject = validated_data.get("high_school_subject", tutor_detail.high_school_subject)
            tutor_detail.diploma_type = validated_data.get("diploma_type", tutor_detail.diploma_type)
            tutor_detail.proficiency_test_type = validated_data.get("proficiency_test_type", tutor_detail.proficiency_test_type)
            tutor_detail.bio = validated_data.get("bio", tutor_detail.bio)
            tutor_detail.max_student_required = validated_data.get("max_student", tutor_detail.max_student_required)
            tutor_detail.allow_intro_call = validated_data.get("allow_intro_call", tutor_detail.allow_intro_call)
            tutor_detail.university_name = validated_data.get("university_name", tutor_detail.university_name)
            tutor_detail.education_status = validated_data.get("education_status", tutor_detail.education_status)
            tutor_detail.discipline = validated_data.get("discipline", tutor_detail.discipline)
            tutor_detail.diploma_grade = validated_data.get("diploma_grade", tutor_detail.diploma_grade)
            tutor_detail.proficiency_test_grade = validated_data.get("proficiency_test_grade", tutor_detail.proficiency_test_grade)
            tutor_detail.hobbies = validated_data.get("hobbies", tutor_detail.hobbies)
            tutor_detail.funfact = validated_data.get("funfact", tutor_detail.funfact)
            tutor_detail.linkedin = validated_data.get("linkedin", tutor_detail.linkedin)
            if diploma_file:
                tutor_detail.diploma_file = diploma_file
            if proficiency_test_file:
                tutor_detail.proficiency_test_file = proficiency_test_file
            if address_front_file:
                tutor_detail.address_front_file = address_front_file
            if address_back_file:
                tutor_detail.address_back_file = address_back_file
            if nationality_front_file:
                tutor_detail.nationality_front_file = nationality_front_file
            if nationality_back_file:
                tutor_detail.nationality_back_file = nationality_back_file

            # tutor_detail.max_hour_class_hour = validated_data.get("max_hour_class_hour", tutor_detail.max_hour_class_hour)
            if subjects:
                tutor_detail.subjects.clear()
                for subject in subjects:
                    tutor_detail.subjects.add(Subject.objects.get(id=subject))
            tutor_detail.save()

            if languages:
                for language in eval(languages):
                    language_id = language["language_id"]
                    language_proficiency = language["proficiency"]

                    try:
                        lang, _ = UserLanguage.objects.get_or_create(user=user, language_id=language_id)
                        lang.proficiency = language_proficiency
                        lang.save()
                    except Exception as err:
                        log_request(f"Error on User Language Creation: {err}")
                        pass
        user.save()
        instance.save()

        return user


class ChangePasswordSerializerIn(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    old_password = serializers.CharField(required=False)
    new_password = serializers.CharField()
    confirm_password = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("user")
        student_id = validated_data.get("user_id")
        old_password = validated_data.get("old_password")
        new_password = validated_data.get("new_password")
        confirm_password = validated_data.get("confirm_password")
        lang = validated_data.get("lang", "en")

        if student_id:
            student = get_object_or_404(Student, user_id=student_id, parent__user=user)
            student.user.password = make_password(password=new_password)
            student.user.save()
            return translate_to_language("Password Reset Successful", lang)

        if not all([old_password, new_password, confirm_password]):
            raise InvalidRequestException({"detail": translate_to_language("All password fields are required", lang)})

        if not check_password(password=old_password, encoded=user.password):
            raise InvalidRequestException({"detail": translate_to_language("Incorrect old password", lang)})

        try:
            validate_password(password=new_password)
        except Exception as err:
            raise InvalidRequestException({'detail': translate_to_language(', '.join(list(err)), lang)})

        if new_password != confirm_password:
            raise InvalidRequestException({"detail": translate_to_language("Passwords mismatch", lang)})

        # Check if new and old passwords are the same
        if old_password == new_password:
            raise InvalidRequestException({"detail": translate_to_language("Same passwords cannot be used", lang)})

        user.password = make_password(password=new_password)
        user.save()

        Thread(target=create_notification, args=[user, translate_to_language("Password changed successfully", lang)]).start()

        return translate_to_language("Password Reset Successful", lang)


class TransactionSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = []


class ChatMessageSerializerOut(serializers.ModelSerializer):
    attachment = serializers.SerializerMethodField()

    def get_attachment(self, obj):
        file = None
        if obj.attachment:
            request = self.context.get("request")
            file = request.build_absolute_uri(obj.attachment.url)
        return file

    class Meta:
        model = ChatMessage
        exclude = []


class ChatMessageSerializerIn(serializers.Serializer):
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receiver_id = serializers.IntegerField()
    message = serializers.CharField(max_length=2000, required=False)
    upload = serializers.FileField(required=False)
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        sender = validated_data.get("sender")
        receiver = validated_data.get("receiver_id")
        message = validated_data.get("message")
        upload = validated_data.get("upload")
        lang = validated_data.get("lang", "en")

        if not any([message, upload]):
            raise InvalidRequestException({"detail": translate_to_language("Text or attachment is required", lang)})

        # Check if student and tutor had previously scheduled classes
        query = Q(tutor_id__in=[sender.id, receiver], student__user_id__in=[sender.id, receiver]) | Q(
            tutor_id__in=[sender.id, receiver], student__parent__user_id__in=[sender.id, receiver])
        if not Classroom.objects.filter(query).exists():
            raise InvalidRequestException({"detail": translate_to_language("Classroom not found for both users", lang)})

        # Send message
        chat = ChatMessage.objects.create(sender=sender, receiver_id=receiver, message=message, attachment=upload)
        return ChatMessageSerializerOut(chat, context={"request": self.context.get("request")}).data


class PaymentPlanSerializerOut(serializers.ModelSerializer):
    average_hour = serializers.SerializerMethodField()

    def get_average_hour(self, obj):
        return round(float(obj.coin) / 7.5)

    class Meta:
        model = PaymentPlan
        exclude = []


class ClassReviewSerializerOut(serializers.ModelSerializer):
    submitted_by = serializers.CharField(source="submitted_by.get_full_name")
    classroom_id = serializers.CharField(source="classroom.id")
    classroom = serializers.CharField(source="classroom.name")

    class Meta:
        model = ClassReview
        exclude = []


class ClassReviewSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    classroom_id = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    content = serializers.CharField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        class_id = validated_data.get("classroom_id")
        title = validated_data.get("title")
        content = validated_data.get("content")
        lang = validated_data.get("lang", "en")

        # Get class
        classroom = get_object_or_404(Classroom, id=class_id)
        if not Classroom.objects.filter(tutor_id__in=[user.id], student__user_id__in=[user.id], id=class_id,
                                        student__parent__user_id__in=[user.id]):
            raise InvalidRequestException({"detail": translate_to_language("Classroom not found/valid", lang)})

        # Create ClassReview
        review, _ = ClassReview.objects.get_or_create(classroom=classroom, submitted_by=user)
        review.title = title
        review.content = content
        review.save()

        return ClassReviewSerializerOut(review).data


class LanguageSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Language
        exclude = []


class SubjectSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Subject
        exclude = []


class NotificationSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Notification
        exclude = []


class UploadProfilePictureSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = serializers.ImageField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        image = validated_data.get("image")

        # Check if authenticated user is a student
        if Student.objects.filter(user=user).exists():
            student = Student.objects.get(user=user)
            student.profile_picture = image
            student.save()
        else:
            user_profile = get_object_or_404(Profile, user=user)
            user_profile.profile_picture = image
            user_profile.save()
        return UserSerializerOut(user, context={"request": self.context.get("request")}).data


class FeedbackAndConsultationSerializerIn(serializers.Serializer):
    request_type = serializers.ChoiceField(choices=CONSULTATION_TYPE_CHOICES)
    full_name = serializers.CharField()
    email_address = serializers.EmailField()
    message = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)
    user_type = serializers.ChoiceField(choices=CONSULTATION_ACCOUNT_TYPE, required=False)

    def create(self, validated_data):
        request_type = validated_data.get("request_type")
        name = validated_data.get("full_name")
        email = validated_data.get("email_address")
        msg = validated_data.get("message")
        user_type = validated_data.get("user_type")
        lang = validated_data.get("lang", "en")
        from edudream.modules.utils import get_site_details
        email_to = str(get_site_details().enquiry_email)

        if request_type == "feedback" and not msg:
            raise InvalidRequestException({"detail": translate_to_language("message is required", lang)})

        if request_type == "consult" and not user_type:
            raise InvalidRequestException({"detail": translate_to_language("User type is required", lang)})

        if request_type == "feedback":
            Thread(target=feedback_email, args=[email_to, name, email, msg, lang]).start()
        if request_type == "consult":
            request_type = "consultation"
            Thread(target=consultation_email, args=[email_to, name, email, user_type, lang]).start()
        return translate_to_language(f"{str(request_type).upper()} submitted successfully", lang)


class TestimonialSerializerOut(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_content(self, obj):
        request = self.context.get("request")
        lang = request.GET.get("lang", "en")
        return translate_to_language(obj.content, lang)

    def get_title(self, obj):
        request = self.context.get("request")
        lang = request.GET.get("lang", "en")
        return translate_to_language(obj.title, lang)

    def get_name(self, obj):
        request = self.context.get("request")
        lang = request.GET.get("lang", "en")
        return translate_to_language(obj.name, lang)

    class Meta:
        model = Testimonial
        exclude = []


class RequestOTPSerializerIn(serializers.Serializer):
    email = serializers.EmailField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        email = validated_data.get("email")
        lang = validated_data.get("lang", "en")

        try:
            user_detail = Profile.objects.get(user__email=email)
        except Profile.DoesNotExist:
            raise InvalidRequestException({"detail": translate_to_language("User not found", lang)})

        expiry = get_next_minute(timezone.now(), 15)
        random_otp = generate_random_otp()
        encrypted_otp = encrypt_text(random_otp)
        user_detail.otp = encrypted_otp
        user_detail.code_expiry = expiry
        user_detail.save()

        # Send OTP to user
        Thread(target=send_otp_token_to_email, args=[user_detail, random_otp, lang]).start()
        return {"detail": translate_to_language("OTP has been sent to your email address", lang), "otp": f"Use this OTP :- {random_otp}. This keyword 'OTP' will be remove before going live"}
        # return translate_to_language("OTP has been sent to your email address", lang)


class ForgotPasswordSerializerIn(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()
    lang = serializers.CharField(required=False)

    def create(self, validated_data):
        email = validated_data.get('email')
        otp = validated_data.get('otp')
        password = validated_data.get('new_password')
        confirm_password = validated_data.get('confirm_password')
        lang = validated_data.get('lang')

        try:
            user_detail = Profile.objects.get(user__email=email)
        except Profile.DoesNotExist:
            raise InvalidRequestException({"detail": translate_to_language("User not found", lang)})

        if timezone.now() > user_detail.code_expiry:
            raise InvalidRequestException({"detail": translate_to_language("OTP has expired, Please request for another one", lang)})

        if otp != decrypt_text(user_detail.otp):
            raise InvalidRequestException({"detail": translate_to_language("Invalid OTP", lang)})

        try:
            validate_password(password=password)
        except Exception as err:
            raise InvalidRequestException({'detail': translate_to_language(', '.join(list(err)), lang)})

        if password != confirm_password:
            raise InvalidRequestException({"detail": translate_to_language("Passwords does not match", lang)})

        user_detail.user.password = make_password(password)
        user_detail.user.save()

        return translate_to_language("Password reset successful", lang)


class UpdateEndedClassroomSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    completed = serializers.BooleanField(default=False)
    reason = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        user = validated_data.get("auth_user")
        completed = validated_data.get("completed")
        reason = validated_data.get("reason")
        lang = validated_data.get("lang")

        if (instance.student_complete_check and instance.tutor_complete_check) or instance.status == "completed":
            raise InvalidRequestException({"detail": translate_to_language("Ended Class already marked as completed", lang)})

        if completed:
            if instance.student.user == user or instance.student.parent.user == user:
                instance.student_complete_check = True
            elif instance.tutor == user:
                instance.tutor_complete_check = True
            else:
                raise InvalidRequestException({"detail": translate_to_language("Permission denied", lang)})

            instance.save()
        else:
            # Create Dispute
            if not reason:
                raise InvalidRequestException({"detail": translate_to_language("Reason is required", lang)})

            dispute, _ = Dispute.objects.get_or_create(submitted_by=user, title=f"Classroom: {instance.name}, marked as uncompleted")
            dispute.dispute_type = "others"
            dispute.content = reason
            dispute.save()
        # Check if both student and tutor complete checks are marked. Then change classroom status to completed
        if instance.tutor_complete_check and instance.student_complete_check:
            instance.status = "completed"
            instance.save()

        return translate_to_language("Thank you for your feedback", lang)




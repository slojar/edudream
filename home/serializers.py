from threading import Thread

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from edudream.modules.choices import ACCOUNT_TYPE_CHOICES
from edudream.modules.email_template import tutor_register_email, parent_register_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.utils import generate_random_otp, log_request, encrypt_text, get_next_minute, password_checker
from home.models import Profile, Wallet, Transaction, ChatMessage
from location.models import Country, State, City
from student.models import Student
from tutor.models import TutorDetail
from tutor.serializers import TutorDetailSerializerOut


class ProfileSerializerOut(serializers.ModelSerializer):
    wallet_balance = serializers.SerializerMethodField()

    def get_wallet_balance(self, obj):
        return Wallet.objects.filter(user=obj.user).last().balance

    class Meta:
        model = Profile
        exclude = []


class UserSerializerOut(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()
    is_tutor = serializers.SerializerMethodField()
    is_student = serializers.SerializerMethodField()

    def get_user_detail(self, obj):
        try:
            return ProfileSerializerOut(Profile.objects.get(user=obj)).data
        except Profile.DoesNotExist:
            return None

    def get_is_student(self, obj):
        if Student.objects.filter(user=obj).exists():
            student = Student.objects.get(user=obj)
            parent = student.parent
            return {
                "dob": student.dob,
                "grade": student.grade,
                "address": parent.address,
                "city_id": parent.city_id,
                "state_id": parent.state_id,
                "country_id": parent.country_id,
                "city_name": parent.city.name,
                "state_name": parent.state.name,
                "country_name": parent.country.name,
                "full_address": parent.get_full_address(),
                "parent_name": parent.get_full_name(),
                "parent_email": parent.email(),
                "parent_mobile": parent.mobile_number
            }
        return False

    def get_is_tutor(self, obj):
        try:
            return TutorDetailSerializerOut(TutorDetail.objects.get(user=obj)).data
        except TutorDetail.DoesNotExist:
            return False

    class Meta:
        model = User
        exclude = ["is_staff", "is_active", "is_superuser", "password", "groups", "user_permissions"]


class SignUpSerializerIn(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email_address = serializers.EmailField()
    password = serializers.CharField()
    address = serializers.CharField(max_length=300)
    account_type = serializers.ChoiceField(choices=ACCOUNT_TYPE_CHOICES)
    mobile_number = serializers.CharField(max_length=20)
    dob = serializers.DateTimeField(required=False)
    city = serializers.IntegerField()
    state = serializers.IntegerField()
    country = serializers.IntegerField()
    bio = serializers.CharField(required=False)
    hobbies = serializers.CharField(required=False)
    funfact = serializers.CharField(required=False)
    linkedin = serializers.CharField(required=False)
    education_status = serializers.CharField(required=False)
    university_name = serializers.CharField(required=False)
    discipline = serializers.CharField(required=False)
    diploma_type = serializers.CharField(required=False)
    diploma_file = serializers.FileField(required=False)
    proficiency_test_type = serializers.CharField(required=False)
    proficiency_test_file = serializers.FileField(required=False)

    def create(self, validated_data):
        f_name = validated_data.get("first_name")
        l_name = validated_data.get("last_name")
        email = validated_data.get("email_address")
        password = validated_data.get("password")
        acct_type = validated_data.get("account_type")
        address = validated_data.get("address")
        phone_number = validated_data.get("mobile_number")
        d_o_b = validated_data.get("dob")
        city_id = validated_data.get("city")
        state_id = validated_data.get("state")
        country_id = validated_data.get("country")
        bio = validated_data.get("bio")
        hobbies = validated_data.get("hobbies")
        funfact = validated_data.get("funfact")
        linkedin = validated_data.get("linkedin")
        education_status = validated_data.get("education_status")
        university_name = validated_data.get("university_name")
        discipline = validated_data.get("discipline")
        diploma_type = validated_data.get("diploma_type")
        diploma_file = validated_data.get("diploma_file")
        proficiency_test_type = validated_data.get("proficiency_test_type")
        proficiency_test_file = validated_data.get("proficiency_test_file")
        required_for_tutor = [
            bio, hobbies, funfact, linkedin, education_status, university_name, discipline, diploma_type, diploma_file,
            proficiency_test_type, proficiency_test_file
        ]
        if acct_type == "tutor" and not all(required_for_tutor):
            raise InvalidRequestException({"detail": "Please submit all required details"})
        country = get_object_or_404(Country, id=country_id)
        state = get_object_or_404(State, id=state_id, country_id=country_id)
        city = get_object_or_404(City, id=city_id, state_id=state_id)

        if User.objects.filter(username__iexact=email).exists():
            raise InvalidRequestException({"detail": "Email is taken"})

        if User.objects.filter(email__iexact=email).exists():
            raise InvalidRequestException({"detail": "Email is taken"})

        try:
            validate_password(password=password)
        except Exception as err:
            raise InvalidRequestException({'detail': ', '.join(list(err))})

        # if password != password_confirm:
        #     raise InvalidRequestException({'detail': 'Passwords mismatch'})

        email_token = generate_random_otp()
        log_request(f"Email Token for email - {email}: {email_token}")

        user, _ = User.objects.get_or_create(username=email)
        user.email = email
        user.first_name = f_name
        user.last_name = l_name
        user.set_password(raw_password=password)
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        if d_o_b:
            profile.dob = d_o_b
        profile.country = country
        profile.state = state
        profile.city = city
        profile.mobile_number = phone_number
        profile.address = address
        profile.account_type = acct_type
        profile.email_verified_code = encrypt_text(email_token)
        profile.code_expiry = get_next_minute(timezone.now(), 15)
        profile.save()

        # Create Wallet
        Wallet.objects.get_or_create(user=user)

        # Create TutorDetail if account type is "tutor"
        if acct_type == "tutor":
            tutor_detail = TutorDetail.objects.get_or_create(user=user)
            tutor_detail.bio = bio
            tutor_detail.hobbies = hobbies
            tutor_detail.funfact = funfact
            tutor_detail.linkedin = linkedin
            tutor_detail.education_status = education_status
            tutor_detail.university_name = university_name
            tutor_detail.discipline = discipline
            tutor_detail.diploma_type = diploma_type
            tutor_detail.diploma_file = diploma_file
            tutor_detail.proficiency_test_type = proficiency_test_type
            tutor_detail.proficiency_test_file = proficiency_test_file
            tutor_detail.save()
            # Send Register Email to Tutor
            Thread(target=tutor_register_email, args=[user]).start()
        else:
            # Send Register Email to Parent
            Thread(target=parent_register_email, args=[user]).start()
        # Send Verification token to email

        return UserSerializerOut(user, context=self.context).data


class LoginSerializerIn(serializers.Serializer):
    email_address = serializers.EmailField()
    password = serializers.CharField()

    def create(self, validated_data):
        email = validated_data.get("email_address")
        password = validated_data.get("password")

        user = authenticate(username=email, password=password)
        if not user:
            raise InvalidRequestException({"detail": "Invalid email or password"})

        if Student.objects.filter(user=user).exists():
            student = Student.objects.get(user=user)
            if student.parent.email_verified is False:
                raise InvalidRequestException({
                    "detail": "Parent email is not verified. Please ask parent/guadian to verify their account"
                })
            return user

        user_profile = Profile.objects.get(user=user)
        if not user_profile.email_verified:
            # OTP Timeout
            random_otp = generate_random_otp()
            user_profile.email_verified_code = encrypt_text(random_otp)
            user_profile.code_expiry = get_next_minute(timezone.now(), 15)
            user_profile.save()

            # Send OTP to user
            # Thread(target=send_token_to_email, args=[user_profile]).start()
            raise InvalidRequestException({
                "detail": "Kindly verify account before login. Check email for OTP", "email_verified": False
            })

        return user


class ProfileSerializerIn(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    address = serializers.CharField(max_length=300, required=False)
    mobile_number = serializers.CharField(max_length=20, required=False)
    dob = serializers.DateTimeField(required=False)
    city_id = serializers.IntegerField(required=False)
    state_id = serializers.IntegerField(required=False)
    country_id = serializers.IntegerField(required=False)
    bio = serializers.CharField(required=False)
    max_student = serializers.IntegerField(required=False)
    subject = serializers.ListSerializer(required=False, child=serializers.IntegerField())

    def update(self, instance, validated_data):
        user = validated_data.get("user")
        country_id = validated_data.get("country_id")
        state_id = validated_data.get("state_id")
        city_id = validated_data.get("city_id")
        subjects = validated_data.get("subject")

        instance.address = validated_data.get('address', instance.address)
        instance.mobile_number = validated_data.get('mobile_number', instance.mobile_number)
        instance.dob = validated_data.get('dob', instance.dob)
        if country_id:
            country = get_object_or_404(Country, id=country_id)
            instance.country = country
        if state_id:
            state = get_object_or_404(State, id=state_id)
            instance.state = state
        if city_id:
            city = get_object_or_404(City, id=city_id)
            instance.city = city
        instance.save()

        if instance.account_type == "tutor":
            tutor_detail = TutorDetail.objects.get(user=user)
            tutor_detail.bio = validated_data.get("bio", tutor_detail.bio)
            tutor_detail.max_student_required = validated_data.get("max_student", tutor_detail.max_student_required)
            if subjects:
                tutor_detail.subjects.clear()
                for subject in subjects:
                    tutor_detail.subjects.add(subject)
            tutor_detail.save()

        return user


class ChangePasswordSerializerIn(serializers.Serializer):
    student_password = serializers.CharField(required=False)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def create(self, validated_data):
        user = validated_data.get("user")
        student_pass = validated_data.get("student_password")
        old_password = validated_data.get("old_password")
        new_password = validated_data.get("new_password")
        confirm_password = validated_data.get("confirm_password")

        # user_query = User.objects.filter(id=userId)
        # if not user_query.exists():
        #     raise InvalidRequestException({"detail": "'userId' does not match any user record"})

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

        return "Password Reset Successful"


class TransactionSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = []


class ChatMessageSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        exclude = []


class ChatMessageSerializerIn(serializers.Serializer):
    sender = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receiver_id = serializers.IntegerField()
    message = serializers.CharField(max_length=2000, required=False)
    upload = serializers.FileField(required=False)

    def create(self, validated_data):
        sender = validated_data.get("sender")
        receiver = validated_data.get("receiver_id")
        message = validated_data.get("message")
        upload = validated_data.get("upload")

        if not any([message, upload]):
            raise InvalidRequestException({"detail": "Text or attachment is required"})

        # Send message
        chat = ChatMessage.objects.create(sender=sender, receiver_id=receiver, message=message, attachment=upload)
        return ChatMessageSerializerOut(chat, context={"request": self.context.get("request")}).data







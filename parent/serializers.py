from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.auth.models import User

from edudream.modules.exceptions import InvalidRequestException
from django.contrib.auth.hashers import make_password

from edudream.modules.utils import decrypt_text, encrypt_text, log_request, translate_to_language
from home.models import PaymentPlan, Transaction, UserLanguage
from student.models import Student

from edudream.modules.stripe_api import StripeAPI


class ParentStudentSerializerOut(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.CharField(source="user.email")
    parent_name = serializers.CharField(source="parent.get_full_name")
    help_subject_names = serializers.SerializerMethodField()

    def get_help_subject_names(self, obj):
        return [subject.name for subject in obj.help_subject.all()]

    class Meta:
        model = Student
        exclude = []


class StudentSerializerIn(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    note = serializers.CharField(required=False)
    lang = serializers.CharField(required=False)
    languages = serializers.ListSerializer(child=serializers.DictField(), required=False)
    # dob = serializers.DateTimeField()
    grade = serializers.CharField()
    help_subjects = serializers.ListSerializer(child=serializers.IntegerField(), required=False)

    def create(self, validated_data):
        user = validated_data.get("user")
        password = validated_data.get("password")
        f_name = validated_data.get("first_name")
        l_name = validated_data.get("last_name")
        username = validated_data.get("username")
        student_note = validated_data.get("note")
        languages = validated_data.get("languages")
        lang = validated_data.get("lang", "en")
        # d_o_b = validated_data.get("dob")
        grade = validated_data.get("grade")
        help_subjects = validated_data.get("help_subjects")

        # When creating child as a parent it should be username not email

        # Check if user with email exists
        # if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():

        if not all([password, f_name, l_name, username]):
            raise InvalidRequestException({"detail": translate_to_language("Required fields: First Name, Last Name, Username, Password", lang)})

        if User.objects.filter(username__iexact=username).exists():
            raise InvalidRequestException({"detail": translate_to_language("Username is taken", lang)})

        # Create student user
        student_user = User.objects.create(
            first_name=f_name, last_name=l_name, username=username, password=make_password(password=password)
        )

        if languages:
            for language in languages:
                language_id = language["language_id"]
                language_proficiency = language["proficiency"]

                try:
                    lang, _ = UserLanguage.objects.get_or_create(user=student_user, language_id=language_id)
                    lang.proficiency = language_proficiency
                    lang.save()
                except Exception as err:
                    log_request(f"Error on User Language Creation: {err}")
                    pass

        # Create student instance
        student = Student.objects.create(user=student_user, grade=grade, note_to_tutor=student_note, parent_id=user.profile.id)
        if help_subjects:
            student.help_subject.clear()
            for subject in help_subjects:
                student.help_subject.add(subject)

        return ParentStudentSerializerOut(student, context={"request": self.context.get("request")}).data

    def update(self, instance, validated_data):
        instance.user.first_name = validated_data.get("first_name", instance.user.first_name)
        instance.user.last_name = validated_data.get("last_name", instance.user.last_name)
        # instance.dob = validated_data.get("dob", instance.dob)
        instance.grade = validated_data.get("grade", instance.grade)
        instance.user.save()
        instance.save()

        return ParentStudentSerializerOut(instance, context={"request": self.context.get("request")}).data


class FundWalletSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    plan_id = serializers.IntegerField()
    ip_address = serializers.IPAddressField()
    redirect_language = serializers.CharField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        plan_id = validated_data.get("plan_id")
        ip_address = validated_data.get("ip_address")
        request = self.context.get("request")
        language = validated_data.get("redirect_language", "en")
        callback_url = request.build_absolute_uri(f'/payment-verify?lang={language}')

        # card_id = validated_data.get("card_id", None)

        plan = get_object_or_404(PaymentPlan, id=plan_id)
        amount = float(plan.amount)
        if not user.profile.stripe_customer_id:
            customer = StripeAPI.create_customer(
                name=user.get_full_name(),
                email=user.email,
                phone=user.profile.mobile_number
            )
            new_stripe_customer_id = customer.get('id')
            user.profile.stripe_customer_id = new_stripe_customer_id
            user.profile.save()
        stripe_customer_id = user.profile.stripe_customer_id
        description = translate_to_language(f'Wallet funding: {user.get_full_name()}', language)
        payment_reference = payment_link = None

        # Calculate tax
        tax_amount = StripeAPI.calculate_tax(user.get_full_name(), amount, ip_address)
        total_amount = float(tax_amount.get("amount_total") / 100)
        while True:
            success, response = StripeAPI.create_payment_session(
                name=user.get_full_name(),
                amount=total_amount,
                return_url=callback_url,
                customer_id=stripe_customer_id,
            )
            if 'no such customer' in str(response).lower():
                customer = StripeAPI.create_customer(
                    name=user.get_full_name(),
                    email=user.email,
                    phone=user.profile.mobile_number
                )
                new_stripe_customer_id = customer.get('id')
                user.profile.stripe_customer_id = new_stripe_customer_id
                user.profile.save()
                continue

            if 'total amount must convert to at least' in str(response).lower():
                text = str(response).lower()
                start_index = text.index("converts to approximately")
                approx = text[start_index:]
                response = translate_to_language(f"Amount must convert to at least 50 cents. {amount}EUR  {approx}", language)

            if not success:
                raise InvalidRequestException({'detail': response})
            if not response.get('url'):
                raise InvalidRequestException({'detail': translate_to_language('Payment could not be completed at the moment', language)})

            payment_reference = response.get('payment_intent')
            if not payment_reference:
                payment_reference = response.get('id')
            payment_link = response.get('url')
            break

        # Create Transaction
        Transaction.objects.create(
            user=user, transaction_type="fund_wallet", amount=plan.amount, narration=description,
            reference=payment_reference, plan_id=plan_id
        )

        return payment_link








from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.auth.models import User

from edudream.modules.exceptions import InvalidRequestException
from django.contrib.auth.hashers import make_password

from edudream.modules.utils import decrypt_text, encrypt_text, log_request
from home.models import PaymentPlan, Transaction, UserLanguage
from student.models import Student

from edudream.modules.stripe_api import StripeAPI


class ParentStudentSerializerOut(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.CharField(source="user.email")

    class Meta:
        model = Student
        exclude = []


class StudentSerializerIn(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email_address = serializers.EmailField()
    password = serializers.CharField()
    note = serializers.CharField(required=False)
    languages = serializers.ListSerializer(child=serializers.DictField(), required=False)
    # dob = serializers.DateTimeField()
    grade = serializers.CharField()
    help_subjects = serializers.ListSerializer(child=serializers.IntegerField(), required=False)

    def create(self, validated_data):
        user = validated_data.get("user")
        password = validated_data.get("password")
        f_name = validated_data.get("first_name")
        l_name = validated_data.get("last_name")
        email = validated_data.get("email_address")
        student_note = validated_data.get("note")
        languages = validated_data.get("languages")
        # d_o_b = validated_data.get("dob")
        grade = validated_data.get("grade")
        help_subjects = validated_data.get("help_subjects")

        # Check if user with email exists
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise InvalidRequestException({"detail": "Email is taken"})

        # Create student user
        student_user = User.objects.create(
            first_name=f_name, last_name=l_name, email=email, username=email, password=make_password(password=password)
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
        instance.user.email = validated_data.get("email_address", instance.user.email)
        # instance.dob = validated_data.get("dob", instance.dob)
        instance.grade = validated_data.get("grade", instance.grade)
        instance.user.save()
        instance.save()

        return ParentStudentSerializerOut(instance, context={"request": self.context.get("request")}).data


class FundWalletSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    plan_id = serializers.IntegerField()
    # card_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        plan_id = validated_data.get("plan_id")
        request = self.context.get("request")
        callback_url = request.build_absolute_uri('/payment-verify?')
        ip_address = request.headers.get('ip-address', None) or request.META.get("ip-address", None)
        if not ip_address:
            raise InvalidRequestException({"detail": "Header: ip-address is required"})

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
            user.profile.stripe_customer_id = encrypt_text(new_stripe_customer_id)
            user.profile.save()
        stripe_customer_id = decrypt_text(user.profile.stripe_customer_id)
        description = f'Wallet funding: {user.get_full_name()}'
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
                user.profile.stripe_customer_id = encrypt_text(new_stripe_customer_id)
                user.profile.save()
                continue

            if 'total amount must convert to at least' in str(response).lower():
                text = str(response).lower()
                start_index = text.index("converts to approximately")
                approx = text[start_index:]
                response = f"Amount must convert to at least 50 cents. {amount}EUR  {approx}"

            if not success:
                raise InvalidRequestException({'detail': response})
            if not response.get('url'):
                raise InvalidRequestException({'detail': 'Payment could not be completed at the moment'})

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








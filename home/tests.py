from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from edudream.modules.utils import log_request, encrypt_text
from home.models import Profile, Wallet
from location.models import Country
from student.models import Student
from tutor.models import PayoutRequest, TutorBankAccount, Classroom


class TestHomeTestCase(TestCase):
    def setUp(self):
        external_bank_acct_id = encrypt_text("ba_1OkNmCPQcSE989KDp8qgfmle")
        acct_id = encrypt_text("acct_1OkNm9PQcSE989KD")

        country = Country.objects.create(name="Canada", alpha2code="CA", active=True, currency_code="CAD")
        parent_user = User.objects.create(username="test@email.com", password=make_password("Test@123"))
        tutor_user = User.objects.create(username="test_tutor@email.com", password=make_password("Test@123"))
        student_user = User.objects.create(username="test_student@email.com", password=make_password("Test@123"))
        parent_profile = Profile.objects.create(user=parent_user, mobile_number="08105700750", account_type="parent")
        student = Student.objects.create(user=student_user, parent=parent_profile)
        bank_account = TutorBankAccount.objects.create(user=tutor_user, bank_name="STRIPE TEST BANK", account_number="9878987899", account_name="Test Name", account_type="individual", routing_number="11000-000", country=country, stripe_external_account_id=external_bank_acct_id)
        payout = PayoutRequest.objects.create(user=tutor_user, bank_account=bank_account, coin=3, amount=10)
        Wallet.objects.create(user=parent_user)
        Classroom.objects.create(name="Test Class", description="Test Description", tutor=tutor_user, student=student, start_date="2024-03-23", end_date="2024-03-23", amount=100, meeting_link="https://testurl.com")

    def test_valid_login(self):
        data = {"email_address": "test@email.com", "password": "Test@123"}
        url = reverse("home:login")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_login(self):
        data = {"email_address": "test@email.com", "password": "Testing@123"}
        url = reverse("home:login")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payout_cron(self):
        data = {}
        url = reverse("home:payout")
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_classroom_view(self):
        data = {"tutor_id": 2}
        url = reverse("home:classroom")
        response = self.client.get(url, data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)





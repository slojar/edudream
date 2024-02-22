from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from home.models import Profile, Wallet
from location.models import Country
from student.models import Student
from tutor.models import TutorDetail, TutorBankAccount


class TestStudentTestCase(TestCase):
    def setUp(self):
        country = Country.objects.create(name="Canada", alpha2code="CA", active=True, currency_code="CAD")
        # Create Tutor User
        tutor_user = User.objects.create(username="test_tutor@email.com", password=make_password("Test@123"), email="test_tutor@email.com")
        Profile.objects.create(user=tutor_user, mobile_number="08105700751", account_type="tutor", active=True, country=country)
        Wallet.objects.create(user=tutor_user)
        TutorBankAccount.objects.create(user=tutor_user, bank_name="Test Bank", account_number="3456543")
        tutor_detail = TutorDetail.objects.create(user=tutor_user)

    def test_valid_login(self):
        data = {"email_address": "test_tutor@email.com", "password": "Test@123"}
        url = reverse("home:login")
        response = self.client.post(url, data)
        res = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return res["access_token"]

    def test_delete_account(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        url = reverse("tutor:delete-bank", kwargs={"id": 1})
        response = self.client.delete(url, headers=header_data)
        print(response.headers)
        print(response.status_code)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_bank(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        data = {
            "bank_name": "Test Bank",
            "account_name": "Sunday Olaofe",
            "account_number": "000123456789",
            "routing_number": "11000-000",
            "country_id": 1
        }
        url = reverse("tutor:add-bank")
        response = self.client.post(url, data, headers=header_data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_intro_call(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        data = {"tutor_id": 3, "start_date": "2024-02-15 13:06:30"}
        url = reverse("student:intro-call")
        response = self.client.post(url, data, headers=header_data)
        print(response.headers)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)


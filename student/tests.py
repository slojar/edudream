import json

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from home.models import Profile, Wallet
from location.models import Country
from student.models import Student
from tutor.models import TutorDetail


class TestStudentTestCase(TestCase):
    def setUp(self):
        # Create Student User
        student_user = User.objects.create(username="test@email.com", password=make_password("Test@123"))
        # Create parent User
        country = Country.objects.create(name="Nigeria", alpha2code="NG", active=True)
        parent_user = User.objects.create(username="test_parent@email.com", password=make_password("Test@123"))
        parent_ = Profile.objects.create(user=parent_user, mobile_number="08105700750", account_type="parent", referral_code="123456", email_verified=True, country=country)
        Wallet.objects.create(user=parent_user)
        # Create Tutor User
        tutor_user = User.objects.create(username="test_tutor@email.com", password=make_password("Test@123"))
        Profile.objects.create(user=tutor_user, mobile_number="08105700751", account_type="tutor")
        tutor_detail = TutorDetail.objects.create(user=tutor_user)
        # Create Student Model
        student = Student.objects.create(user=student_user, parent=parent_)

    def test_valid_login(self):
        data = {"email_address": "test@email.com", "password": "Test@123"}
        url = reverse("home:login")
        response = self.client.post(url, data)
        res = response.json()
        # print(res)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return res["access_token"]

    def test_intro_call(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        data = {"tutor_id": 3, "start_date": "2024-02-15 13:06:30"}
        url = reverse("student:intro-call")
        response = self.client.post(url, data, headers=header_data)
        print(response.headers)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)


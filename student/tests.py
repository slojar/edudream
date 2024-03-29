import json

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from home.models import Profile, Wallet, Subject, SiteSetting
from location.models import Country
from student.models import Student
from tutor.models import TutorDetail, TutorCalendar, Classroom


class TestStudentTestCase(TestCase):
    def setUp(self):
        # Create Student User
        student_user = User.objects.create(username="test@email.com", password=make_password("Test@123"), first_name="Test", last_name="Student")
        # Create parent User
        country = Country.objects.create(name="Nigeria", alpha2code="NG", active=True)
        parent_user = User.objects.create(username="test_parent@email.com", password=make_password("Test@123"))
        parent_ = Profile.objects.create(user=parent_user, mobile_number="08105700750", account_type="parent", referral_code="123456", email_verified=True, country=country)
        Wallet.objects.create(user=parent_user, balance=40.0)
        # Create Tutor User
        tutor_user = User.objects.create(username="test_tutor@email.com", password=make_password("Test@123"), first_name="Sunday", last_name="Olaofe")
        Wallet.objects.create(user=tutor_user, balance=40.0)
        Profile.objects.create(user=tutor_user, mobile_number="08105700751", account_type="tutor", active=True)
        tutor_detail = TutorDetail.objects.create(user=tutor_user)
        TutorCalendar.objects.create(user=tutor_user, day_of_the_week=1, time_from="13:00:00", time_to="12:00:00")
        # Create Student Model
        student = Student.objects.create(user=student_user, parent=parent_)
        # Create Subject
        subject = Subject.objects.create(name="Mathematics", grade="high_school", amount=7.0)
        Classroom.objects.create(
            name="Test classroom", description="Test description", tutor=tutor_user, student=student,
            start_date="2024-02-26T13:00:00", end_date="2024-02-26T15:00:00", expected_duration=15, amount=10,
            status="completed", subjects=subject
        )
        SiteSetting.objects.create(site_id=1, zoom_token="gAAAAABl3r3S0Kl21yxs6Mj4c_dLMhHaW-H65vydsUSbYT8hY-KRjlqhNDGGJLIs0haaDYZrajbXDL8rLSVelhC2Xvg6UJcECpvv4posuU6rhZSoGkQ6bMgQNNLT_bhHnP4Utre8GFQiOcufvVGK_3IAb9aFoNyySXxHR3lO0s78TjHa_G7Xs2DQ21m5eUpl4Bz0NnfhFVDsnBkcKCcQKmmKGlkQTJ12ytSJvGR-JdC8mWjj1H7TpAIF0AEHBlWj8D9jChhXqCgAShc7WBGMHegIsn8EdMKGYPkuEIQXFK9XTZiel6NuJ8z92M6Ov5tU7Pf00-dFC35AQbd41wDBxdPt6MAsMSFat0m34uYnGBtp9NXJqhT3NQ9_GqmcNzX7MuX6jU5sWBBV44vXov9sLj10YTHsdZ9ySwfonV_gE0pKEK3p54jFgJVbeh7W-a5-XXMItv0J-gx7vWPxV0HU29CIGm9tkRu1jb-fP-zn_0ZTGMdHTt44v6CQE-rZN-ZFxOuaDOpdzT8Tb--GbAzqx2hdgDLkgPKC59L2U2CHCPjz1lE5mWq-X-FYfFjNqVbdjpWzyY2iC4IFjQ_bcmKfD0WDRoWWiMuATA0IAjRt0abKlV4rSkNRzKmM24lNPX6srG27x7mfH8nn9Tw6XuVy_vuReWMMUTOIEK3tOl44T3W1u6TVywopaC-Pg5vRFO5AWabRX95VcKPawsOdEUh6ccpdPh_umJQOZVgweiI9kwZyei3AMBqEY4S8r2m8pb92XeD3rYJUJp2dMdEtPT2FlsMPBfretmRSMHpwohTy4TGoF1aiYj0gMnVzfFbqwgUrFwdlZSpuSzHxh23xP1Nech60uwhB8nujXA==")

    def test_valid_login(self):
        data = {"email_address": "test_tutor@email.com", "password": "Test@123"}
        url = reverse("home:login")
        response = self.client.post(url, data)
        res = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return res["access_token"]

    def test_intro_call(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        data = {"tutor_id": 3, "start_date": "2024-02-15 13:06:30"}
        url = reverse("student:intro-call")
        response = self.client.post(url, data, headers=header_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_class(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        data = {
            "name": "First Class Booking",
            "description": "Just teach him good english",
            "tutor_id": 3,
            "student_id": 1,
            "start_date": "2024-02-26T13:00:00",
            "end_date": "2024-02-26T15:00:00",
            "subject_id": 1,
            "book_now": False
        }
        url = reverse("student:create-classroom")
        response = self.client.post(url, data, headers=header_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_class_status_change(self):
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}", "Content-Type": "application/json"}
        raw_data = {"action": "accept"}
        data = json.dumps(raw_data)
        url = reverse("tutor:classroom-status", kwargs={"pk": 1})
        response = self.client.put(url, data, headers=header_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_chat_list(self):
        url = reverse("home:chat-list")
        header_data = {"Authorization": f"Bearer {self.test_valid_login()}"}
        response = self.client.get(url, headers=header_data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_200_OK)




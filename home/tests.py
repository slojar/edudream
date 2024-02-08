from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from edudream.modules.utils import log_request
from home.models import Profile, Wallet


class TestHomeTestCase(TestCase):
    def setUp(self):
        parent_user = User.objects.create(username="test@email.com", password=make_password("Test@123"))
        Profile.objects.create(user=parent_user, mobile_number="08105700750", account_type="parent")
        Wallet.objects.create(user=parent_user)

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






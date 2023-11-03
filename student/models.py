
from django.db import models
from django.contrib.auth.models import User

from home.models import Profile


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(Profile, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="student-pictures", blank=True, null=True)
    dob = models.DateTimeField(blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username



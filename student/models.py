
from django.db import models
from django.contrib.auth.models import User

from home.models import Profile


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent = models.ForeignKey(Profile, on_delete=models.CASCADE)
    dob = models.DateTimeField(blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username




from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    parent = models.ForeignKey("home.Profile", on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to="student-pictures", blank=True, null=True)
    dob = models.DateTimeField(blank=True, null=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    help_subject = models.ManyToManyField("home.Subject")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username



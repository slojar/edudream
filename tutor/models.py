from django.db import models
from django.contrib.auth.models import User

from home.models import Subject


class Tutor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    subjects = models.ManyToManyField(Subject)
    max_student_required = models.IntegerField(default=10)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"


class Classroom(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=300)
    tutor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="parent")
    student = models.ForeignKey(User, related_name="class_student", on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    completed = models.BooleanField(default=False)
    meeting_link = models.CharField(max_length=300, blank=True, null=True)
    subjects = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tutor.username}: {self.name} - {self.amount}"


class ClassDocument(models.Model):
    tutor = models.ForeignKey(User, on_delete=models.CASCADE)
    class_room = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    file = models.FileField(upload_to="subject-document")
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tutor.username}: {self.class_room.name}"

# Questions:
# 1. Can Tutor create a class for more than one student at a time?
# 2. Can more than one subject be taught in a single class


class StudentRating(models.Model):
    tutor = models.ForeignKey(User, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="student")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=True, null=True)
    rating = models.IntegerField(default=0)
    review = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {}".format(self.tutor.username, self.student.username)




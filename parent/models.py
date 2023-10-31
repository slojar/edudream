from django.contrib.auth.models import User
from django.db import models


class TutorRating(models.Model):
    parent = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tutor_to_rate")
    rating = models.IntegerField(default=0)
    headline = models.CharField(max_length=250)
    review = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {}".format(self.parent.username, self.tutor.username)



from rest_framework import serializers
from tutor.models import TutorDetail


class TutorDetailSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = TutorDetail
        exclude = ["user"]







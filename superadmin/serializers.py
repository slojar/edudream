from django.contrib.auth import authenticate
from rest_framework import serializers

from edudream.modules.exceptions import InvalidRequestException
from home.serializers import TutorListSerializerOut


class TutorStatusSerializerIn(serializers.Serializer):
    active = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance.active = validated_data.get("active", instance.active)
        instance.save()
        return TutorListSerializerOut(instance, context={"request": self.context.get("request")}).data


class AdminLoginSerializerIn(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def create(self, validated_data):
        username = validated_data.get("username")
        password = validated_data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            raise InvalidRequestException({"detail": "Invalid login credentials"})

        return user




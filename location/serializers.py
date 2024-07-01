from rest_framework import serializers
from .models import *


class StateSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()

    class Meta:
        model = State
        exclude = []


class CountryWithStatesSerializer(serializers.ModelSerializer):
    states = serializers.SerializerMethodField()

    def get_states(self, obj):
        state = None
        if State.objects.filter(country=obj, active=True).exists():
            state = StateSerializer(State.objects.filter(country=obj, active=True), many=True).data
        return state

    class Meta:
        model = Country
        exclude = []


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        exclude = []





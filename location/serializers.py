from rest_framework import serializers
from .models import *


class CitySerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)

    class Meta:
        model = City
        exclude = []


class StateSerializer(serializers.ModelSerializer):
    cities = serializers.SerializerMethodField()

    def get_cities(self, obj):
        cities = None
        if City.objects.filter(state=obj, state__active=True).exists():
            cities = CitySerializer(City.objects.filter(state=obj, state__active=True), many=True,
                                    context={'request': self.context.get('request')}).data
        return cities

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





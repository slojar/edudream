from threading import Thread

from django.shortcuts import HttpResponse, get_object_or_404

from edudream.modules.paginations import CustomPagination
from .models import *
from rest_framework.views import APIView
from .serializers import CountrySerializer, StateSerializer
from rest_framework import generics

from edudream.modules.utils import create_country_state_city


class CountryListAPIView(generics.ListAPIView):
    permission_classes = []
    serializer_class = CountrySerializer
    queryset = Country.objects.filter(active=True)


class StateListAPIView(generics.ListAPIView):
    permission_classes = []
    pagination_class = CustomPagination
    serializer_class = StateSerializer

    def get_queryset(self):
        country_id = self.request.GET.get("country_id")
        country = get_object_or_404(Country, id=country_id, active=True)
        return State.objects.filter(country=country, active=True)


class PopulateLocationAPIView(APIView):
    permission_classes = []

    def get(self, request):
        Thread(target=create_country_state_city, args=[]).start()
        return HttpResponse("<h4>Populating Location Data</h4>")


from threading import Thread

from django.shortcuts import HttpResponse, get_object_or_404
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from edudream.modules.paginations import CustomPagination
from .models import *
from rest_framework.views import APIView
from .serializers import CountrySerializer, StateSerializer
from rest_framework import generics, filters

from edudream.modules.utils import create_country_state_city


class CountryListAPIView(generics.ListAPIView):
    permission_classes = []
    serializer_class = CountrySerializer
    # queryset = Country.objects.filter(active=True)
    queryset = Country.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(name='country_id', description='Country Id', type=int),
        ]
    )
)
class StateListAPIView(generics.ListAPIView):
    permission_classes = []
    pagination_class = CustomPagination
    serializer_class = StateSerializer

    def get_queryset(self):
        country_id = self.request.GET.get("country_id")
        country = get_object_or_404(Country, id=country_id)
        return State.objects.filter(country=country)


class PopulateLocationAPIView(APIView):
    permission_classes = []

    def get(self, request):
        Thread(target=create_country_state_city, args=[]).start()
        return HttpResponse("<h4>Populating Location Data</h4>")


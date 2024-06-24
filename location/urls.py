from django.urls import path
from . import views

app_name = 'location'
urlpatterns = [
    path('country', views.CountryListAPIView.as_view(), name='country'),
    path('state', views.StateListAPIView.as_view(), name='state'),
    path('city', views.CityListAPIView.as_view(), name='city'),
    path('create-location', views.PopulateLocationAPIView.as_view(), name='create-location'),
]

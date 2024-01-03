from django.urls import path
from . import views

app_name = "tutor"

urlpatterns = [
    path('classroom', views.TutorClassRoomAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.TutorClassRoomAPIView.as_view(), name="classroom-detail"),
    path('dispute', views.DisputeAPIView.as_view(), name="dispute"),
    path('dispute/<int:pk>', views.DisputeAPIView.as_view(), name="dispute-detail"),
]


from django.urls import path
from . import views

app_name = "tutor"

urlpatterns = [
    path('classroom', views.TutorClassRoomAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.TutorClassRoomAPIView.as_view(), name="classroom-detail"),
    path('classroom-status', views.UpdateClassroomStatusAPIView.as_view(), name="classroom-status"),
    path('dispute', views.DisputeAPIView.as_view(), name="dispute"),
    path('dispute/<int:pk>', views.DisputeAPIView.as_view(), name="dispute-detail"),
    path('create-dispute', views.CreateDisputeAPIView.as_view(), name="create-dispute"),
    path('calendar', views.TutorCalendarListAPIView.as_view(), name="list-calendar"),
    path('add-calendar', views.TutorCalendarAPIView.as_view(), name="add-to-calendar"),
]


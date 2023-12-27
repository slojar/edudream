from django.urls import path
from . import views

app_name = "tutor"

urlpatterns = [
    path('classroom', views.TutorClassRoomAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.TutorClassRoomAPIView.as_view(), name="classroom-detail"),
    # path('login/', views.LoginAPIView.as_view(), name="login"),
]


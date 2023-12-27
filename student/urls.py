from django.urls import path
from . import views

app_name = "student"

urlpatterns = [
    path('classroom', views.StudentClassRoomAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.StudentClassRoomAPIView.as_view(), name="classroom-details"),
    # path('login/', views.LoginAPIView.as_view(), name="login"),
]


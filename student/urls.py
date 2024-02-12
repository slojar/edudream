from django.urls import path
from . import views

app_name = "student"

urlpatterns = [
    path('classroom', views.StudentClassRoomAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.StudentClassRoomAPIView.as_view(), name="classroom-details"),
    path('create-classroom', views.CreateClassRoomAPIView.as_view(), name="create-classroom"),
    path('intro-call', views.IntroCallAPIView.as_view(), name="intro-call"),
    # path('login/', views.LoginAPIView.as_view(), name="login"),
]


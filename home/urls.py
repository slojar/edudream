from django.urls import path
from . import views
from django.http.response import JsonResponse


def homepage(request):
    return JsonResponse({"message": "Welcome to EduDream Backend"})


app_name = "home"

urlpatterns = [
    path('', homepage),
    # path('create-user/', views.CreateUserAPIView.as_view(), name="create-user"),
    # path('login/', views.LoginAPIView.as_view(), name="login"),
]


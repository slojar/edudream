from django.urls import path
from . import views
from django.http.response import JsonResponse


def homepage(request):
    return JsonResponse({"message": "Welcome to EduDream Backend"})


app_name = "home"

urlpatterns = [
    path('', homepage),
    path('signup', views.SignUpAPIView.as_view(), name="signup"),
    path('login', views.LoginAPIView.as_view(), name="login"),
    path('profile', views.ProfileAPIView.as_view(), name="profile"),
    path('change-password', views.ChangePasswordAPIView.as_view(), name="change-password"),
    path('payment-history', views.PaymentHistoryAPIView.as_view(), name="payment"),
    path('chat', views.ChatMessageAPIView.as_view(), name="chat"),
]


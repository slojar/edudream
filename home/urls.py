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
    path('payment-plans', views.PaymentPlanListAPIView.as_view(), name="payment-plan"),
    path('submit-review', views.SubmitReviewAPIView.as_view(), name="submit-review"),
    path('payment-verify', views.VerifyPaymentAPIView.as_view(), name="payment-verify"),
    path('tutor-list', views.TutorListAPIView.as_view(), name="tutors"),
    path('language', views.LanguageListAPIView.as_view(), name="language"),
    path('subjects', views.SubjectListAPIView.as_view(), name="subjects"),
    path('notification', views.NotificationAPIView.as_view(), name="notification"),
    path('notification/<int:pk>', views.NotificationAPIView.as_view(), name="notification-detail"),
    path('upload-avatar', views.UploadProfilePictureAPIView.as_view(), name="upload-avatar"),
]


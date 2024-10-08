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
    path('email-verification', views.EmailVerificationLinkView.as_view(), name="email-verification"),
    path('resend-verification', views.RequestEmailVerificationLinkView.as_view(), name="email-validation"),
    path('profile', views.ProfileAPIView.as_view(), name="profile"),
    path('change-password', views.ChangePasswordAPIView.as_view(), name="change-password"),
    path('payment-history', views.PaymentHistoryAPIView.as_view(), name="payment"),
    path('chat', views.ChatMessageAPIView.as_view(), name="chat"),
    path('payment-plans', views.PaymentPlanListAPIView.as_view(), name="payment-plan"),
    path('submit-review', views.SubmitReviewAPIView.as_view(), name="submit-review"),
    path('payment-verify', views.VerifyPaymentAPIView.as_view(), name="payment-verify"),
    path('tutor-list', views.TutorListAPIView.as_view(), name="tutors"),
    path('tutor-list/<int:pk>', views.TutorListAPIView.as_view(), name="tutors"),
    path('language', views.LanguageListAPIView.as_view(), name="language"),
    path('subjects', views.SubjectListAPIView.as_view(), name="subjects"),
    path('notification', views.NotificationAPIView.as_view(), name="notification"),
    path('notification/<int:pk>', views.NotificationAPIView.as_view(), name="notification-detail"),
    path('upload-avatar', views.UploadProfilePictureAPIView.as_view(), name="upload-avatar"),
    path('feedback', views.FeedBackAndConsultationAPIView.as_view(), name="feedback"),
    path('testimonials', views.TestimonialListAPIView.as_view(), name="testimonial"),
    path('classroom', views.TutorClassroomListAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.UpdateEndedClassroomAPIView.as_view(), name="classroom-update"),
    path('request-otp', views.RequestOTPView.as_view(), name="request-otp"),
    path('reset-password', views.ForgotPasswordView.as_view(), name="reset-password"),
    path('chat-list', views.ChatListAPIView.as_view(), name="chat-list"),

    # CRON-JOBS
    path('refresh-zoom', views.RefreshZoomTokenCronAPIView.as_view(), name="zoom-refresh"),
    path('payout', views.PayoutProcessingCronAPIView.as_view(), name="payout"),
    path('reminder', views.ClassEventReminderCronAPIView.as_view(), name="reminder"),
    path('pending-balance', views.UpdateTutorPendingBalanceCronAPIView.as_view(), name="pending-balance"),
    path('main-balance', views.UpdateTutorMainBalanceCronAPIView.as_view(), name="main-balance"),
    path('ended-classroom', views.UpdateEndedClassroomCronAPIView.as_view(), name="ended-classroom"),
    # path('payout', views.PayoutProcessingCronAPIView.as_view(), name="payout"),

    # WEBHOOK
    path('webhook', views.WebhookAPIView.as_view(), name="webhook"),
]


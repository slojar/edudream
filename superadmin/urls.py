from django.urls import path
from . import views

app_name = "superadmin"

urlpatterns = [
    path('login', views.AdminLoginAPIView.as_view(), name="login"),
    path('dashboard', views.DashboardAPIView.as_view(), name="dashboard"),
    path('tutor', views.TutorListAPIVIew.as_view(), name="tutor"),
    path('tutor/<int:pk>', views.TutorListAPIVIew.as_view(), name="tutor-detail"),
    path('tutor-status/<int:pk>', views.UpdateTutorStatusAPIView.as_view(), name="tutor-status"),
    path('parent', views.ParentListAPIView.as_view(), name="parent"),
    path('parent/<int:pk>', views.ParentListAPIView.as_view(), name="parent-detail"),
    path('classroom', views.ClassRoomListAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.ClassRoomListAPIView.as_view(), name="classroom-detail"),
    path('reviews', views.ClassReviewListAPIView.as_view(), name="review"),
    path('reviews/<int:id>', views.ClassReviewRetrieveAPIView.as_view(), name="review-detail"),
    path('add-payment-plan', views.PaymentPlanCreateAPIView.as_view(), name="create-payment-plan"),
    path('payment-plan', views.PaymentPlanListAPIView.as_view(), name="payment-plan"),
    path('payment-plan/<int:id>', views.PaymentPlanRetrieveUpdateDeleteAPIView.as_view(), name="payment-plan-detail"),
    path('add-language', views.LanguageCreateAPIView.as_view(), name="add-language"),
    path('language', views.LanguageListAPIView.as_view(), name="language"),
    path('language/<int:id>', views.LanguageDeleteAPIView.as_view(), name="delete-language"),
    path('message', views.NotificationListAPIView.as_view(), name="message"),
    path('send-message', views.SendNotificationAPIView.as_view(), name="send-message"),
    path('change-password', views.AdminChangePasswordAPIView.as_view(), name="change-password"),
    path('payout', views.PayoutListAPIView.as_view(), name="payout"),
    path('payout/<int:pk>', views.PayoutListAPIView.as_view(), name="payout-detail"),
    path('update-payout/<int:pk>', views.ApprovePayoutRequestAPIView.as_view(), name="approve-decline-payout"),
    path('dispute', views.DisputeAPIView.as_view(), name="dispute"),
    path('dispute/<int:pk>', views.DisputeAPIView.as_view(), name="dispute-detail"),
    path('sitesettings', views.SiteSettingsAPIView.as_view(), name="site-settings"),
    path('subject', views.AdminSubjectAPIView.as_view(), name="subjects"),
    path('subject/<int:pk>', views.AdminSubjectDetailAPIView.as_view(), name="subject-detail"),

]


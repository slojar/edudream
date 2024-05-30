from django.urls import path
from . import views

app_name = "tutor"

urlpatterns = [
    path('classroom', views.TutorClassRoomAPIView.as_view(), name="classroom"),
    path('custom-classroom', views.CustomClassAPIView.as_view(), name="classroom"),
    path('classroom/<int:pk>', views.TutorClassRoomAPIView.as_view(), name="classroom-detail"),
    path('classroom-status/<int:pk>', views.UpdateClassroomStatusAPIView.as_view(), name="classroom-status"),
    path('dispute', views.DisputeAPIView.as_view(), name="dispute"),
    path('dispute/<int:pk>', views.DisputeAPIView.as_view(), name="dispute-detail"),
    path('create-dispute', views.CreateDisputeAPIView.as_view(), name="create-dispute"),
    path('calendar', views.TutorCalendarListAPIView.as_view(), name="list-calendar"),
    path('add-calendar', views.TutorCalendarAPIView.as_view(), name="add-to-calendar"),
    # path('add-bank', views.CreateBankAccountAPIView.as_view(), name="add-bank"),
    # path('delete-bank/<int:id>', views.DeleteBankAccountAPIView.as_view(), name="delete-bank"),
    path('create-payout', views.CreateTutorPayoutAPIView.as_view(), name="create-payout"),
    path('payout', views.TutorPayoutAPIView.as_view(), name="payout"),
    path('payout/<int:pk>', views.TutorPayoutAPIView.as_view(), name="payout-detail"),
    path('add-subject', views.CreateTutorSubjectAPIView.as_view(), name="create-subject"),
    path('subject', views.TutorSubjectListAPIView.as_view(), name="subject"),
    path('upload-subject-file', views.UploadSubjectDocumentCreateAPIView.as_view(), name="subject-file-upload"),
    path('onboarding', views.GetOnboardingLinkView.as_view(), name="onboarding"),

]


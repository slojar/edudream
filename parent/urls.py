from django.urls import path
from . import views

app_name = "parent"

urlpatterns = [
    path('student/', views.ListStudentAPIView.as_view(), name="student"),
    path('student/<int:id>/', views.RetrieveDeleteStudent.as_view(), name="retrieve-student"),
    path('create-student/', views.CreateStudentAPIView.as_view(), name="create-student"),
    path('update-student/<int:pk>/', views.EditStudentAPIView.as_view(), name="update-student"),
]


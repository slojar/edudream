from rest_framework.permissions import BasePermission

from home.models import Profile
from student.models import Student
from tutor.models import TutorDetail


class IsParent(BasePermission):
    def has_permission(self, request, view):
        try:
            parent = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return False
        if parent.account_type == "parent":
            return True
        else:
            return False


class IsTutor(BasePermission):
    def has_permission(self, request, view):
        try:
            TutorDetail.objects.get(user=request.user)
            return True
        except TutorDetail.DoesNotExist:
            return False


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return False
        if student.parent.email_verified:
            return True
        else:
            return False




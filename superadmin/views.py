from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView, \
    RetrieveAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from home.models import Profile, ClassReview, PaymentPlan, Language, Notification
from home.serializers import ProfileSerializerOut, TutorListSerializerOut, ClassReviewSerializerOut, \
    PaymentPlanSerializerOut, LanguageSerializerOut, NotificationSerializerOut
from parent.serializers import ParentStudentSerializerOut
from student.models import Student
from superadmin.serializers import TutorStatusSerializerIn, AdminLoginSerializerIn, NotificationSerializerIn
from tutor.models import Classroom
from tutor.serializers import ClassRoomSerializerOut


class DashboardAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = dict()
        students = Student.objects.all()
        profiles = Profile.objects.all()
        parents = profiles.filter(account_type="parent")
        tutors = profiles.filter(account_type="tutor")

        data["total_student_count"] = students.count()
        data["total_parent_count"] = parents.count()
        data["total_tutor_count"] = tutors.count()
        data["recent_tutors"] = TutorListSerializerOut(
            tutors.filter(active=True, user__tutordetail__isnull=False).order_by("-id")[:10], many=True, context={"request": request}).data
        data["recent_parents"] = ProfileSerializerOut(
            parents.filter(user__tutordetail__isnull=True).order_by("-id")[:10], many=True).data
        data["recent_students"] = ParentStudentSerializerOut(students.order_by("-id")[:10], many=True, context={"request": request}).data
        return Response({"detail": "Success", "data": data})


class TutorListAPIVIew(APIView, CustomPagination):
    permission_classes = [IsAdminUser]

    @extend_schema(parameters=[OpenApiParameter(name="search", type=str), OpenApiParameter(name="subject_id", type=str),
                               OpenApiParameter(name="date_from", type=str), OpenApiParameter(name="diploma_grade", type=str),
                               OpenApiParameter(name="date_to", type=str), OpenApiParameter(name="disploma_type", type=str)])
    def get(self, request, pk=None):
        search = request.GET.get("search")
        subject = request.GET.get("subject_id", list())
        diploma_grade = request.GET.get("diploma_grade")
        diploma_type = request.GET.get("disploma_type")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if pk:
            queryset = get_object_or_404(Profile, id=pk, account_type="tutor")
            serializer = TutorListSerializerOut(queryset, context={"request": request}).data
            return Response({"detail": "Success", "data": serializer})

        query = Q(account_type="tutor")
        if search:
            query &= Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | \
                     Q(user__email__icontains=search)
        if subject:
            query &= Q(user__tutordetail__subjects__in=subject)
        if diploma_grade:
            query &= Q(user__tutordetail__diploma_grade__iexact=diploma_grade)
        if diploma_type:
            query &= Q(user__tutordetail__diploma_type__iexact=diploma_type)
        if date_from and date_to:
            query &= Q(user__date_joined__range=[date_from, date_to])

        queryset = self.paginate_queryset(Profile.objects.filter(query).order_by("-id").distinct(), request)
        serializer = TutorListSerializerOut(queryset, many=True, context={"request": request}).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class UpdateTutorStatusAPIView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=TutorStatusSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        tutor = get_object_or_404(Profile, account_type="tutor", id=pk)
        serializer = TutorStatusSerializerIn(instance=tutor, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Tutor status updated", "data": response})


class AdminLoginAPIView(APIView):
    permission_classes = []

    @extend_schema(request=AdminLoginSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = AdminLoginSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response({"detail": "Login Successful",  "access_token": f"{AccessToken.for_user(user)}"})


class ParentListAPIView(APIView, CustomPagination):
    permission_classes = [IsAdminUser]

    @extend_schema(parameters=[OpenApiParameter(name="search", type=str), OpenApiParameter(name="date_from", type=str),
                               OpenApiParameter(name="date_to", type=str)])
    def get(self, request, pk=None):
        search = request.GET.get("search")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if pk:
            queryset = get_object_or_404(Profile, id=pk, account_type="parent")
            serializer = ProfileSerializerOut(queryset, context={"request": request}).data
            return Response({"detail": "Success", "data": serializer})

        query = Q(account_type="parent")
        if search:
            query &= Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | \
                     Q(user__email__icontains=search)
        if date_from and date_to:
            query &= Q(user__date_joined__range=[date_from, date_to])

        queryset = self.paginate_queryset(Profile.objects.filter(query).order_by("-id").distinct(), request)
        serializer = ProfileSerializerOut(queryset, many=True, context={"request": request}).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class ClassRoomListAPIView(APIView, CustomPagination):
    permission_classes = [IsAdminUser]

    @extend_schema(parameters=[OpenApiParameter(name="search", type=str), OpenApiParameter(name="date_from", type=str),
                               OpenApiParameter(name="date_to", type=str)])
    def get(self, request, pk=None):
        search = request.GET.get("search")
        subject_name = request.GET.get("subject_name")
        grade = request.GET.get("grade")
        class_status = request.GET.get("status")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        # amount_from = request.GET.get("amount_from")
        # amount_to = request.GET.get("amount_to")

        if pk:
            queryset = get_object_or_404(Classroom, id=pk)
            serializer = ClassRoomSerializerOut(queryset, context={"request": request}).data
            return Response({"detail": "Success", "data": serializer})

        query = Q()
        if search:
            query &= Q(name__icontains=search) | Q(tutor__last_name__icontains=search) | \
                     Q(student__user__last_name__icontains=search)
        if subject_name:
            query &= Q(subjects__name__iexact=subject_name)
        if grade:
            query &= Q(subjects__grade__iexact=grade)
        if class_status:
            query &= Q(status=class_status)
        if date_from and date_to:
            query &= Q(created_on__range=[date_from, date_to])
        # if amount_to and amount_from:
        #     query &= Q()

        queryset = self.paginate_queryset(Classroom.objects.filter(query).order_by("-id").distinct(), request)
        serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class ClassReviewListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    queryset = ClassReview.objects.all().order_by("-id")
    serializer_class = ClassReviewSerializerOut
    filter_backends = [SearchFilter]
    search_fields = ["classroom__name", "submitted_by__first_name", "submitted_by__last_name", "title"]


class ClassReviewRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAdminUser]
    queryset = ClassReview.objects.all()
    serializer_class = ClassReviewSerializerOut
    lookup_field = "id"


class PaymentPlanCreateAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanSerializerOut


class PaymentPlanRetrieveUpdateDeleteAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanSerializerOut
    lookup_field = "id"


class PaymentPlanListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = PaymentPlan.objects.all().order_by("-id")
    serializer_class = PaymentPlanSerializerOut
    pagination_class = CustomPagination


class LanguageCreateAPIView(CreateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Language.objects.all()
    serializer_class = LanguageSerializerOut


class LanguageListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Language.objects.all().order_by("-id")
    serializer_class = LanguageSerializerOut


class LanguageDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAdminUser]
    queryset = Language.objects.all()
    serializer_class = LanguageSerializerOut
    lookup_field = "id"


class NotificationListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = Notification.objects.all().order_by("-id")
    serializer_class = NotificationSerializerOut
    pagination_class = CustomPagination


class SendNotificationAPIView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=NotificationSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = NotificationSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Notification created",  "data": response})




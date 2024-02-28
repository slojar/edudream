from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsParent
from student.models import Student
from parent.serializers import ParentStudentSerializerOut, StudentSerializerIn, FundWalletSerializerIn
from tutor.models import Classroom
from tutor.serializers import ClassRoomSerializerOut


class CreateStudentAPIView(APIView):
    permission_classes = [IsAuthenticated & IsParent]

    @extend_schema(request=StudentSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = StudentSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Student account created", "data": response})


class EditStudentAPIView(APIView):
    permission_classes = [IsAuthenticated & IsParent]

    @extend_schema(request=StudentSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        instance = get_object_or_404(Student, parent__user=request.user, id=int(pk))
        serializer = StudentSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Student updated", "data": response})


class RetrieveDeleteStudent(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated & IsParent]
    serializer_class = ParentStudentSerializerOut
    lookup_field = "id"

    def get_queryset(self):
        return Student.objects.filter(parent__user=self.request.user)


class ListStudentAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated & IsParent]
    serializer_class = ParentStudentSerializerOut
    queryset = Student.objects.filter()
    pagination_class = CustomPagination

    def get_queryset(self):
        return Student.objects.filter(parent__user=self.request.user)


class FundWalletAPIView(APIView):
    permission_classes = [IsAuthenticated & IsParent]

    @extend_schema(request=FundWalletSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = FundWalletSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Payment link generated", "data": response})


class ParentStudentClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & IsParent]

    @extend_schema(
        parameters=[OpenApiParameter(name="status", type=str), OpenApiParameter(name="date_from", type=str),
                    OpenApiParameter(name="date_to", type=str)]
    )
    def get(self, request, pk=None):
        if pk:
            item = get_object_or_404(Classroom, id=pk, student__parent__user=request.user)
            response = ClassRoomSerializerOut(item, context={"request": request}).data
        else:
            class_status = request.GET.get("status")
            search = request.GET.get("search")
            date_from = request.GET.get("date_from")
            date_to = request.GET.get("date_to")
            student_id = request.GET.get("student_id")
            query = Q(student__parent__user=request.user)

            if search:
                query &= Q(name__icontains=search) | Q(tutor__last_name__icontains=search) | \
                         Q(tutor__first_name__icontains=search) | Q(subjects__name__icontains=search) | \
                         Q(student__user__first_name__icontains=search)
            if student_id:
                query &= Q(student__user_id=student_id)
            if class_status:
                query &= Q(status=class_status)
            if date_from and date_to:
                query &= Q(start_date__range=[date_from, date_to])

            queryset = self.paginate_queryset(Classroom.objects.filter(query), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})



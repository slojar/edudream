from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsParent
from home.models import Transaction
from student.models import Student
from parent.serializers import ParentStudentSerializerOut, StudentSerializerIn, FundWalletSerializerIn


class CreateStudentAPIView(APIView):
    permission_classes = [IsParent]

    @extend_schema(request=StudentSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = StudentSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Student account created", "data": response})


class EditStudentAPIView(APIView):
    permission_classes = [IsParent]

    @extend_schema(request=StudentSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        instance = get_object_or_404(Student, parent__user=request.user, id=int(pk))
        serializer = StudentSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Student updated", "data": response})


class RetrieveDeleteStudent(generics.RetrieveDestroyAPIView):
    permission_classes = [IsParent]
    serializer_class = ParentStudentSerializerOut
    lookup_field = "id"

    def get_queryset(self):
        return Student.objects.filter(parent__user=self.request.user)


class ListStudentAPIView(generics.ListAPIView):
    permission_classes = [IsParent]
    serializer_class = ParentStudentSerializerOut
    queryset = Student.objects.filter()
    pagination_class = CustomPagination

    def get_queryset(self):
        return Student.objects.filter(parent__user=self.request.user)


class FundWalletAPIView(APIView):
    permission_classes = [IsParent]

    @extend_schema(request=FundWalletSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = FundWalletSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Payment link generated", "data": response})




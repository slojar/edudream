from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsStudent
from tutor.models import Classroom
from tutor.serializers import CreateClassSerializerIn, ClassRoomSerializerOut


class StudentClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsStudent]

    def get(self, request, pk=None):
        if pk:
            item = get_object_or_404(Classroom, id=pk, student__user=request.user)
            response = ClassRoomSerializerOut(item, context={"request": request}).data
        else:
            queryset = self.paginate_queryset(Classroom.objects.filter(student__user=request.user), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})

    @extend_schema(request=CreateClassSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = CreateClassSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response({
            "detail": "Classroom request sent successfully",
            "data": ClassRoomSerializerOut(user, context={"request": request}).data
        })




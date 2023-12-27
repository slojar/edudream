from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor
from tutor.models import Classroom
from tutor.serializers import ApproveDeclineClassroomSerializerIn, ClassRoomSerializerOut


class TutorClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsTutor]

    def get(self, request, pk=None):
        if pk:
            item = get_object_or_404(Classroom, id=pk, tutor=request.user)
            response = ClassRoomSerializerOut(item, context={"request": request}).data
        else:
            queryset = self.paginate_queryset(Classroom.objects.filter(tutor=request.user), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})

    @extend_schema(request=ApproveDeclineClassroomSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        instance = get_object_or_404(Classroom, id=pk, tutor=request.user)
        serializer = ApproveDeclineClassroomSerializerIn(
            instance=instance, data=request.data, context={'request': request}
        )
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)




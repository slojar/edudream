from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsStudent, IsParent
from tutor.models import Classroom
from tutor.serializers import CreateClassSerializerIn, ClassRoomSerializerOut


class StudentClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & IsStudent]

    @extend_schema(
        parameters=[OpenApiParameter(name="status", type=str), OpenApiParameter(name="date_from", type=str),
                    OpenApiParameter(name="date_to", type=str)]
    )
    def get(self, request, pk=None):
        if pk:
            item = get_object_or_404(Classroom, id=pk, student__user=request.user)
            response = ClassRoomSerializerOut(item, context={"request": request}).data
        else:
            class_status = request.GET.get("status")
            date_from = request.GET.get("date_from")
            date_to = request.GET.get("date_to")
            query = Q(student__user=request.user)
            if class_status:
                query &= Q(status=class_status)
            if date_from and date_to:
                query &= Q(created_on__range=[date_from, date_to])

            queryset = self.paginate_queryset(Classroom.objects.filter(query), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class CreateClassRoomAPIView(APIView):
    permission_classes = [IsAuthenticated & (IsStudent | IsParent)]

    @extend_schema(request=CreateClassSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = CreateClassSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)




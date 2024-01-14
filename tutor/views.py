from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor
from tutor.models import Classroom, Dispute, TutorCalendar
from tutor.serializers import ApproveDeclineClassroomSerializerIn, ClassRoomSerializerOut, DisputeSerializerIn, \
    DisputeSerializerOut, TutorCalendarSerializerIn, TutorCalendarSerializerOut


class TutorClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsTutor]

    @extend_schema(parameters=[OpenApiParameter(name="completed", type=str)])
    def get(self, request, pk=None):
        if pk:
            item = get_object_or_404(Classroom, id=pk, tutor=request.user)
            response = ClassRoomSerializerOut(item, context={"request": request}).data
        else:
            completed = request.GET.get("completed")
            query = Q(tutor=request.user)
            if completed == "true":
                query &= Q(completed=True)
            queryset = self.paginate_queryset(Classroom.objects.filter(query), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class UpdateClassroomStatusAPIView(APIView):
    permission_classes = [IsTutor]

    @extend_schema(request=ApproveDeclineClassroomSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        instance = get_object_or_404(Classroom, id=pk, tutor=request.user)
        serializer = ApproveDeclineClassroomSerializerIn(
            instance=instance, data=request.data, context={'request': request}
        )
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)


class DisputeAPIView(APIView, CustomPagination):
    permission_classes = [IsTutor]

    @extend_schema(
        parameters=[OpenApiParameter(name="status", type=str), OpenApiParameter(name="search", type=str),
                    OpenApiParameter(name="dispute_type", type=str)]
    )
    def get(self, request, pk=None):
        if pk:
            dispute = get_object_or_404(Dispute, id=pk, submitted_by=request.user)
            response = DisputeSerializerOut(dispute, context={"request": request}).data
        else:
            d_status = request.GET.get("status")
            search = request.GET.get("search")
            d_type = request.GET.get("dispute_type")
            query = Q(submitted_by=request.user)
            if d_status:
                query &= Q(status=d_status)
            if search:
                query &= Q(title__icontains=search) | Q(content__icontains=search)
            if d_type:
                query &= Q(dispute_type=d_type)
            queryset = self.paginate_queryset(Dispute.objects.filter(query), request)
            serializer = DisputeSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Dispute(s) Retrieved", "data": response})

    @extend_schema(request=DisputeSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        instance = get_object_or_404(Dispute, id=pk, submitted_by=request.user)
        serializer = DisputeSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Dispute updated", "data": response})


class CreateDisputeAPIView(APIView):
    permission_classes = [IsTutor]

    @extend_schema(request=DisputeSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = DisputeSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Dispute created successfully", "data": response})


class TutorCalendarAPIView(APIView):
    permission_classes = [IsTutor]

    @extend_schema(request=TutorCalendarSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = TutorCalendarSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Calendar updated", "data": response})


@extend_schema(parameters=[OpenApiParameter(name="tutor_id", type=str)])
class TutorCalendarListAPIView(ListAPIView):
    permission_classes = []
    serializer_class = TutorCalendarSerializerOut

    def get_queryset(self):
        tutor_id = self.kwargs.get("tutor_id")
        return TutorCalendar.objects.filter(user_id=tutor_id)




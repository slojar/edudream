from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor
from tutor.models import Classroom, Dispute, TutorCalendar, PayoutRequest, TutorSubject, TutorSubjectDocument, \
    TutorBankAccount
from tutor.serializers import ApproveDeclineClassroomSerializerIn, ClassRoomSerializerOut, DisputeSerializerIn, \
    DisputeSerializerOut, TutorCalendarSerializerIn, TutorCalendarSerializerOut, TutorBankAccountSerializerIn, \
    RequestPayoutSerializerIn, PayoutSerializerOut, TutorSubjectSerializerIn, TutorSubjectSerializerOut, \
    TutorSubjectDocumentSerializerIn, TutorBankAccountSerializerOut, CustomClassSerializerIn


class CustomClassAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=CustomClassSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = CustomClassSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)


class TutorClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(
        parameters=[OpenApiParameter(name="status", type=str), OpenApiParameter(name="date_from", type=str),
                    OpenApiParameter(name="date_to", type=str)]
    )
    def get(self, request, pk=None):
        if pk:
            item = get_object_or_404(Classroom, id=pk, tutor=request.user)
            response = ClassRoomSerializerOut(item, context={"request": request}).data
        else:
            class_status = request.GET.get("status")
            date_from = request.GET.get("date_from")
            date_to = request.GET.get("date_to")
            query = Q(tutor=request.user)
            if class_status:
                query &= Q(status=class_status)
            if date_from and date_to:
                query &= Q(start_date__range=[date_from, date_to])
            queryset = self.paginate_queryset(Classroom.objects.filter(query), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class UpdateClassroomStatusAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

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
    permission_classes = [IsAuthenticated & IsTutor]

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
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=DisputeSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = DisputeSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Dispute created successfully", "data": response})


class TutorCalendarAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=TutorCalendarSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = TutorCalendarSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Calendar updated", "data": response})


@extend_schema(parameters=[OpenApiParameter(name="tutor_id", type=str)])
class TutorCalendarListAPIView(ListAPIView):
    permission_classes = []
    serializer_class = TutorCalendarSerializerOut

    def get_queryset(self):
        tutor_id = self.request.GET.get("tutor_id")
        return TutorCalendar.objects.filter(user_id=tutor_id)


class CreateBankAccountAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=TutorBankAccountSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = TutorBankAccountSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Success", "data": response})


class TutorPayoutAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(parameters=[OpenApiParameter(name="status", type=str)])
    def get(self, request, pk=None):
        if pk:
            payout = get_object_or_404(PayoutRequest, id=pk, user=request.user)
            response = PayoutSerializerOut(payout).data
        else:
            d_status = request.GET.get("status")
            query = Q(user=request.user)
            if d_status:
                query &= Q(status=d_status)
            queryset = self.paginate_queryset(PayoutRequest.objects.filter(query), request)
            serializer = PayoutSerializerOut(queryset, many=True).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": "Payout(s) Retrieved", "data": response})


class CreateTutorPayoutAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=RequestPayoutSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = RequestPayoutSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)


class CreateTutorSubjectAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=TutorSubjectSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = TutorSubjectSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": "Success", "data": response})


class TutorSubjectListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated & IsTutor]
    serializer_class = TutorSubjectSerializerOut

    def get_queryset(self):
        return TutorSubject.objects.filter(user=self.request.user)


class UploadSubjectDocumentCreateAPIView(CreateAPIView):
    permission_classes = [IsAuthenticated & IsTutor]
    serializer_class = TutorSubjectDocumentSerializerIn
    queryset = TutorSubjectDocument.objects.all()


class DeleteBankAccountAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated & IsTutor]
    serializer_class = TutorBankAccountSerializerOut
    lookup_field = "id"

    def get_queryset(self):
        # bank_id = self.kwargs.get("id")
        return TutorBankAccount.objects.filter(user=self.request.user)



from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from edudream.modules.exceptions import raise_serializer_error_msg, InvalidRequestException
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor, IsStudent, IsParent
from edudream.modules.stripe_api import StripeAPI
from edudream.modules.utils import translate_to_language, log_request
from edudream.settings.base import BASE_DIR
from home.models import Profile
from student.models import Student
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
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response({"detail": translate_to_language("Custom class created successfully", request.data.get("lang", "en")), "data": response})


class TutorClassRoomAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(
        parameters=[OpenApiParameter(name="status", type=str), OpenApiParameter(name="date_from", type=str),
                    OpenApiParameter(name="date_to", type=str)]
    )
    def get(self, request, pk=None):
        lang = request.GET.get("lang", "en")
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
                # query &= Q(start_date__range=[date_from, date_to])
                query &= Q(start_date__gte=date_from, start_date__lte=date_to)
            queryset = self.paginate_queryset(Classroom.objects.filter(query).order_by("-id"), request)
            if class_status == "accepted":
                queryset = self.paginate_queryset(Classroom.objects.filter(query).exclude(tutor_complete_check=True).order_by("-id"), request)
            serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
            response = self.get_paginated_response(serializer).data
        return Response({"detail": translate_to_language("Success", lang), "data": response})


class UpdateClassroomStatusAPIView(APIView):
    permission_classes = [IsAuthenticated & (IsTutor | IsStudent | IsParent)]

    @extend_schema(request=ApproveDeclineClassroomSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        action = request.data.get("action")
        lang = request.GET.get("lang", "en")
        if Profile.objects.filter(user=request.user, account_type="parent").exists():
            if action == "cancel":
                return Response({"detail": translate_to_language("You are not permitted to perform this action", lang)},
                                status=status.HTTP_400_BAD_REQUEST)
            instance = get_object_or_404(Classroom, id=pk, student__parent__user=request.user)
        elif Student.objects.filter(user=request.user).exists():
            if action == "cancel":
                return Response({"detail": translate_to_language("You are not permitted to perform this action", lang)},
                                status=status.HTTP_400_BAD_REQUEST)
            instance = get_object_or_404(Classroom, id=pk, student__user=request.user)
        elif Profile.objects.filter(user=request.user, account_type="tutor").exists():
            instance = get_object_or_404(Classroom, id=pk, tutor=request.user)
        else:
            return Response({"detail": translate_to_language("Classroom not found", lang)}, status=status.HTTP_400_BAD_REQUEST)
        # if action == "cancel" and (IsStudent or IsParent):
        #     return Response({"detail": translate_to_language("You are not permitted to perform this action", lang)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ApproveDeclineClassroomSerializerIn(
            instance=instance, data=request.data, context={'request': request}
        )
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response(response)


class DisputeAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(
        parameters=[OpenApiParameter(name="status", type=str), OpenApiParameter(name="search", type=str),
                    OpenApiParameter(name="dispute_type", type=str)]
    )
    def get(self, request, pk=None):
        lang = request.GET.get("lang", "en")
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
        return Response({"detail": translate_to_language("Dispute(s) Retrieved", lang), "data": response})

    @extend_schema(request=DisputeSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request, pk):
        instance = get_object_or_404(Dispute, id=pk, submitted_by=request.user)
        serializer = DisputeSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response({"detail": translate_to_language("Dispute updated", request.data.get("lang", "en")), "data": response})


class CreateDisputeAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=DisputeSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = DisputeSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response({"detail": translate_to_language("Dispute created successfully", request.data.get("lang", "en")), "data": response})


class TutorCalendarAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=TutorCalendarSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = TutorCalendarSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response(response)


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
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response(response)


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
        return Response({"detail": translate_to_language("Payout(s) Retrieved", request.GET.get("lang", "en")), "data": response})


class CreateTutorPayoutAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=RequestPayoutSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = RequestPayoutSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response(response)


class CreateTutorSubjectAPIView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    @extend_schema(request=TutorSubjectSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = TutorSubjectSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors, language=request.data.get("lang", "en"))
        response = serializer.save()
        return Response({"detail": translate_to_language("Success", request.data.get("lang", "en")), "data": response})


class TutorSubjectListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated & IsTutor]
    serializer_class = TutorSubjectSerializerOut

    def get_queryset(self):
        return TutorSubject.objects.filter(user=self.request.user)


class TutorSubjectDeleteAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated & IsTutor]
    serializer_class = TutorSubjectSerializerOut
    lookup_field = "id"

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


class GetOnboardingLinkView(APIView):
    permission_classes = [IsAuthenticated & IsTutor]

    def get(self, request):
        lang = request.GET.get("lang", "en")
        tutor = get_object_or_404(Profile, user=request.user, account_type="tutor")
        try:
            # Address and Nationality Documents
            address_front_file = tutor.user.tutordetail.address_front_file
            address_back_file = tutor.user.tutordetail.address_back_file
            nat_front_file = tutor.user.tutordetail.nationality_front_file
            nat_back_file = tutor.user.tutordetail.nationality_back_file

            if not all([address_front_file, address_back_file, nat_front_file, nat_back_file]):
                raise InvalidRequestException({
                    "detail": translate_to_language(
                        "Please upload address and proof of identity document in your profile setting", lang)
                })

            address_front = str(BASE_DIR) + str(address_front_file.url)
            address_back = str(BASE_DIR) + str(address_back_file.url)
            nat_front = str(BASE_DIR) + str(nat_front_file.url)
            nat_back = str(BASE_DIR) + str(nat_back_file.url)

            if not tutor.stripe_connect_account_id:
                # Create Connect Account for Tutor
                connect_account = StripeAPI.create_connect_account(request.user)
                connect_account_id = connect_account.get("id")
                tutor.stripe_connect_account_id = connect_account_id
                tutor.save()

            # Update account with documents
            if tutor.stripe_connect_account_id and not tutor.stripe_documents_uploaded:
                # Upload AddressFrontDocument
                addr_front_upload = StripeAPI.upload_file(address_front, "identity_document")
                addr_front_file_id = addr_front_upload.get("id")
                # Upload AddressBackDocument
                addr_back_upload = StripeAPI.upload_file(address_back, "identity_document")
                addr_back_file_id = addr_back_upload.get("id")
                # Upload NationalityFrontDocument
                nat_front_upload = StripeAPI.upload_file(nat_front, "identity_document")
                nat_front_file_id = nat_front_upload.get("id")
                # Upload NationalityBackDocument
                nat_back_upload = StripeAPI.upload_file(nat_back, "identity_document")
                nat_back_file_id = nat_back_upload.get("id")

                StripeAPI.update_connect_account(
                    request.user, addr_front_file_id, addr_back_file_id, nat_front_file_id, nat_back_file_id
                )
                # Mark documents as uploaded
                tutor.stripe_documents_uploaded = True
                tutor.save()

            stripe_connected_acct = tutor.stripe_connect_account_id
            # Generate Onboarding Link
            response = StripeAPI.create_account_link(acct=stripe_connected_acct)
            url = response.get("url")
            return Response({"detail": "Link generated", "onboarding_link": url})
        except Exception as err:
            log_request(f"Error while performing Connect Onboarding:\n{err}")
            raise InvalidRequestException({"detail": translate_to_language("An error has occurred, please try again later", lang)})


class TutorActiveClassroomAPIView(APIView):
    permission_classes = []

    @extend_schema(
        parameters=[OpenApiParameter(name="tutor_id", type=str), OpenApiParameter(name="date_from", type=str),
                    OpenApiParameter(name="date_to", type=str)]
    )
    def get(self, request):
        tutor_id = request.GET.get("tutor_id")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        allowed_status = ["accepted", "new"]
        if not tutor_id:
            raise InvalidRequestException({"detail": translate_to_language("TutorID required")})

        query = Q(tutor_id=tutor_id) & Q(status__in=allowed_status)
        if date_from and date_to:
            query &= Q(start_date__gte=date_from, start_date__lte=date_to)
        queryset = Classroom.objects.filter(query).order_by("-id")
        serializer = ClassRoomSerializerOut(queryset, many=True, context={"request": request}).data
        return Response(serializer)


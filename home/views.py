import ast
import logging

from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.filters import SearchFilter

from edudream.modules.cron import zoom_login_refresh, payout_cron_job
from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor, IsParent, IsStudent
from edudream.modules.utils import complete_payment, get_site_details
from home.models import Profile, Transaction, ChatMessage, PaymentPlan, Language, Subject, Notification, Testimonial
from home.serializers import SignUpSerializerIn, LoginSerializerIn, UserSerializerOut, ProfileSerializerIn, \
    ChangePasswordSerializerIn, TransactionSerializerOut, ChatMessageSerializerIn, ChatMessageSerializerOut, \
    PaymentPlanSerializerOut, ClassReviewSerializerIn, TutorListSerializerOut, LanguageSerializerOut, \
    SubjectSerializerOut, NotificationSerializerOut, UploadProfilePictureSerializerIn, \
    FeedbackAndConsultationSerializerIn, TestimonialSerializerOut, RequestOTPSerializerIn, ForgotPasswordSerializerIn
from tutor.models import Classroom
from tutor.serializers import ClassRoomSerializerOut


class SignUpAPIView(APIView):
    permission_classes = []

    @extend_schema(request=SignUpSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = SignUpSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)


class LoginAPIView(APIView):
    permission_classes = []

    @extend_schema(request=LoginSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = LoginSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response({
            "detail": "Login Successful", "data": UserSerializerOut(user, context={"request": request}).data,
            "access_token": f"{AccessToken.for_user(user)}"
        })


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated & (IsTutor | IsParent | IsStudent)]

    def get(self, request):
        return Response(
            {"detail": "Success", "data": UserSerializerOut(request.user, context={"request": request}).data})

    @extend_schema(request=ProfileSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request):
        instance = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response(
            {"detail": "Profile updated", "data": UserSerializerOut(user, context={"request": request}).data})


class ChangePasswordAPIView(APIView):
    permission_classes = []

    @extend_schema(request=ChangePasswordSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = ChangePasswordSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})


@extend_schema_view(get=extend_schema(parameters=[
    OpenApiParameter(name='type', type=str), OpenApiParameter(name='amount_from', type=str),
    OpenApiParameter(name='amount_to', type=str), OpenApiParameter(name='date_from', type=str),
    OpenApiParameter(name='status', type=str)]))
class PaymentHistoryAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated & (IsTutor | IsParent)]

    def get(self, request, pk=None):
        trans_type = request.GET.get("type")
        amount_from = request.GET.get("amount_from")
        amount_to = request.GET.get("amount_to")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        trans_status = request.GET.get("status")

        query = Q(user=request.user)

        if pk:
            queryset = get_object_or_404(Transaction, id=pk, user=request.user)
            serializer = TransactionSerializerOut(queryset).data
            return Response({"detail": "Success", "data": serializer})

        if amount_to and amount_from:
            query &= Q(amount__range=[amount_from, amount_to])

        if date_to and date_from:
            query &= Q(created_on__range=[date_from, date_to])

        if trans_status:
            query &= Q(status=trans_status)

        if trans_type:
            query &= Q(transaction_type=trans_type)

        queryset = self.paginate_queryset(Transaction.objects.filter(query).exclude(status="pending"), request)
        serializer = TransactionSerializerOut(queryset, many=True).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


# @extend_schema_view(get=extend_schema(parameters=[
#     OpenApiParameter(name='receiver_id', type=str), OpenApiParameter(name='search', type=str)]))
class ChatMessageAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChatMessageSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = ChatMessageSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})

    @extend_schema(
        parameters=[OpenApiParameter(name="receiver_id", type=str), OpenApiParameter(name="search", type=str)]
    )
    def get(self, request):
        receiver_id = request.GET.get("receiver_id")
        search = request.GET.get("search")
        sender = request.user
        # Fetch messages
        query = Q(sender_id__in=[sender.id, receiver_id], receiver_id__in=[receiver_id, sender.id])
        if search:
            query &= Q(message__icontains=search)
        messages = ChatMessage.objects.filter(query).distinct().order_by("-created_on")
        messages.update(read=True)
        queryset = self.paginate_queryset(messages, request)
        serializer = ChatMessageSerializerOut(queryset, many=True, context={"request": request}).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Chat retrieved", "data": response})


class PaymentPlanListAPIView(ListAPIView):
    permission_classes = []
    queryset = PaymentPlan.objects.all().order_by("-created_on")
    serializer_class = PaymentPlanSerializerOut


class SubmitReviewAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=ClassReviewSerializerIn, responses={status.HTTP_201_CREATED})
    def post(self, request):
        serializer = ClassReviewSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})


class VerifyPaymentAPIView(APIView):
    permission_classes = []

    @extend_schema(parameters=[OpenApiParameter(name="reference", type=str), OpenApiParameter(name="lang", type=str)])
    def get(self, request):
        site_setting = get_site_details()
        frontend_base_url = site_setting.frontend_url
        reference = request.GET.get("reference")
        language = request.GET.get("lang")
        success, response = complete_payment(reference)
        if success is False:
            return HttpResponseRedirect(
                redirect_to=f"{frontend_base_url}/verify-checkout?lang={language}&status={str(success).lower()}")
        #     return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
        return HttpResponseRedirect(
            redirect_to=f"{frontend_base_url}/verify-checkout?lang={language}&status={str(success).lower()}")


class TutorListAPIView(APIView, CustomPagination):
    permission_classes = []

    @extend_schema(
        parameters=[OpenApiParameter(name="search", type=str), OpenApiParameter(name="country", type=str),
                    OpenApiParameter(name="grade", type=str), OpenApiParameter(name="diploma_type", type=str),
                    OpenApiParameter(name="university_name", type=str)]
    )
    def get(self, request):
        search = request.GET.get("search")  # Tutor name Subject name
        country = request.GET.get("country", list())  # Arrays of ID
        grade = request.GET.get("grade")  # Subject grades
        diploma_type = request.GET.get("diploma_type")  # diploma_type
        university_name = request.GET.get("university_name")  # university_name

        query = Q(account_type="tutor", active=True)

        if search:
            school_subject_name = [item for item in Subject.objects.filter(name__icontains=search)]
            query &= Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search) | Q(
                user__tutordetail__subjects__in=school_subject_name)
        if country:
            country_ids = ast.literal_eval(str(country))
            query &= Q(country_id__in=country_ids)
        if grade:
            school_grade_subject = [item for item in Subject.objects.filter(grade__exact=grade)]
            query &= Q(user__tutordetail__subjects__in=school_grade_subject)
        if diploma_type:
            query &= Q(user__tutordetail__diploma_type__iexact=diploma_type)
        if university_name:
            query &= Q(user__tutordetail__university_name__icontains=university_name)

        queryset = self.paginate_queryset(Profile.objects.filter(query).order_by("?"), request)
        serializer = TutorListSerializerOut(queryset, many=True, context={"request": request}).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Tutor retrieved", "data": response})


class LanguageListAPIView(ListAPIView):
    permission_classes = []
    queryset = Language.objects.all().order_by("name")
    serializer_class = LanguageSerializerOut


class SubjectListAPIView(ListAPIView):
    permission_classes = []
    queryset = Subject.objects.filter(active=True).order_by("name")
    serializer_class = SubjectSerializerOut
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ["name", "grade"]


class NotificationAPIView(APIView, CustomPagination):
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[OpenApiParameter(name="readall", type=str)])
    def get(self, request, pk=None):
        readall = request.GET.get("readall")
        query = Notification.objects.filter(user__in=[request.user])
        if pk:
            query = Notification.objects.filter(id=pk, user__in=[request.user])
            query.update(read=True)
        if readall:
            query.update(read=True)

        queryset = self.paginate_queryset(Notification.objects.filter(user__in=[request.user]).order_by("-id"), request)
        serializer = NotificationSerializerOut(queryset, many=True).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


class UploadProfilePictureAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=UploadProfilePictureSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = UploadProfilePictureSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})


class FeedBackAndConsultationAPIView(APIView):
    permission_classes = []

    @extend_schema(request=FeedbackAndConsultationSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = FeedbackAndConsultationSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})


@extend_schema(parameters=[OpenApiParameter(name="language", type=str)])
class TestimonialListAPIView(ListAPIView):
    permission_classes = []
    serializer_class = TestimonialSerializerOut

    def get_queryset(self):
        lang = self.request.GET.get("language", "french")
        return Testimonial.objects.filter(language=lang).order_by("?")


@extend_schema(parameters=[OpenApiParameter(name="tutor_id", type=str)])
class TutorClassroomListAPIView(ListAPIView):
    permission_classes = []
    serializer_class = ClassRoomSerializerOut

    def get_queryset(self):
        tutor_id = self.request.GET.get("tutor_id")
        return Classroom.objects.filter(tutor_id=tutor_id)


class RequestOTPView(APIView):
    permission_classes = []

    @extend_schema(request=RequestOTPSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = RequestOTPSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        # return Response({"detail": response})
        return Response(response)


class ForgotPasswordView(APIView):
    permission_classes = []

    @extend_schema(request=ForgotPasswordSerializerIn, responses={status.HTTP_200_OK})
    def post(self, request):
        serializer = ForgotPasswordSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})


# CRON
class RefreshZoomTokenCronAPIView(APIView):
    permission_classes = []

    def get(self, request):
        from edudream.modules.utils import get_site_details, encrypt_text
        d_site = get_site_details()
        response = zoom_login_refresh()
        access_token = response["access_token"]
        d_site.zoom_token = encrypt_text(access_token)
        d_site.save()
        return JsonResponse({"detail": "Cron Ran Successfully"})


class ChatListAPIView(APIView):
    permission_classes = [IsAuthenticated & (IsStudent | IsTutor)]

    def get(self, request):
        # Get all users logged in user can chat with
        result = list()
        if IsStudent:
            all_classroom = Classroom.objects.filter(status__in=["accepted", "completed", "cancelled"],
                                                     student__user=request.user)
            for tut in all_classroom:
                message = None
                date_created = None
                if ChatMessage.objects.filter(sender_id__in=[request.user.id, tut.tutor_id],
                                              receiver_id__in=[request.user.id, tut.tutor_id]).exists():
                    chat = ChatMessage.objects.filter(sender_id__in=[request.user.id, tut.tutor_id],
                                                      receiver_id__in=[request.user.id, tut.tutor_id]).last()
                    message = str(chat.message)
                    date_created = chat.created_on
                image = None
                if tut.tutor.profile.profile_picture:
                    image = request.build_absolute_uri(tut.tutor.profile.profile_picture.url)
                user_data = {
                    "user_id": tut.tutor_id,
                    "name": tut.tutor.get_full_name(),
                    "image": image,
                    "last_message": message,
                    "date": date_created
                }
                user_id_exists = any(d["user_id"] == user_data["user_id"] for d in result)

                if not user_id_exists:
                    result.append(user_data)

        if IsTutor:
            all_classroom = Classroom.objects.filter(status__in=["accepted", "completed", "cancelled"],
                                                     tutor=request.user)
            for stu in all_classroom:
                message = None
                date_created = None
                if ChatMessage.objects.filter(sender_id__in=[request.user.id, stu.student.user_id],
                                              receiver_id__in=[request.user.id, stu.student.user_id]).exists():
                    chat = ChatMessage.objects.filter(sender_id__in=[request.user.id, stu.student.user_id],
                                                      receiver_id__in=[request.user.id, stu.student.user_id]).last()
                    date_created = chat.created_on
                    message = str(chat.message)
                image = None
                if stu.student.profile_picture:
                    image = request.build_absolute_uri(stu.student.profile_picture.url)
                user_data = {
                    "user_id": stu.student.user_id,
                    "name": stu.student.user.get_full_name(),
                    "image": image,
                    "last_message": message,
                    "date": date_created
                }
                user_id_exists = any(d["user_id"] == user_data["user_id"] for d in result)

                if not user_id_exists:
                    result.append(user_data)

        return Response({"detail": "Success", "data": result})


class PayoutProcessingCronAPIView(APIView):
    permission_classes = []

    def get(self, request):
        payout_cron_job()
        return JsonResponse({"detail": "Cron Ran Successfully"})

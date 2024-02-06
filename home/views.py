import logging

from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.filters import SearchFilter

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor, IsParent, IsStudent
from edudream.modules.utils import complete_payment, get_site_details
from home.models import Profile, Transaction, ChatMessage, PaymentPlan, Language, Subject, Notification
from home.serializers import SignUpSerializerIn, LoginSerializerIn, UserSerializerOut, ProfileSerializerIn, \
    ChangePasswordSerializerIn, TransactionSerializerOut, ChatMessageSerializerIn, ChatMessageSerializerOut, \
    PaymentPlanSerializerOut, ClassReviewSerializerIn, TutorListSerializerOut, LanguageSerializerOut, \
    SubjectSerializerOut, NotificationSerializerOut, UploadProfilePictureSerializerIn


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
    permission_classes = [IsAuthenticated & (IsTutor | IsParent)]

    def get(self, request):
        return Response({"detail": "Success", "data": UserSerializerOut(request.user, context={"request": request}).data})

    @extend_schema(request=ProfileSerializerIn, responses={status.HTTP_200_OK})
    def put(self, request):
        instance = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response({"detail": "Profile updated", "data": UserSerializerOut(user, context={"request": request}).data})


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

    @extend_schema(parameters=[OpenApiParameter(name="reference", type=str)])
    def get(self, request):
        site_setting = get_site_details()
        frontend_base_url = site_setting.frontend_url
        reference = request.GET.get("reference")
        success, response = complete_payment(reference)
        if success is False:
            return HttpResponseRedirect(
                redirect_to=f"{frontend_base_url}/verify-checkout?status={str(success).lower()}")
        #     return Response({"detail": response}, status=status.HTTP_400_BAD_REQUEST)
        return HttpResponseRedirect(redirect_to=f"{frontend_base_url}/verify-checkout?status={str(success).lower()}")


class TutorListAPIView(ListAPIView):
    permission_classes = []
    queryset = Profile.objects.filter(account_type="tutor", active=True).order_by("?")
    serializer_class = TutorListSerializerOut
    pagination_class = CustomPagination
    filter_backends = [SearchFilter]
    search_fields = ["user__first_name", "user__last_name"]


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

    @extend_schema(parameters=[OpenApiParameter(name="read", type=str)])
    def get(self, request, pk=None):
        if pk:
            queryset = get_object_or_404(Notification, id=pk, user__in=[request.user])
            serializer = NotificationSerializerOut(queryset).data
            return Response({"detail": "Success", "data": serializer})

        queryset = self.paginate_queryset(Notification.objects.filter(user__in=[request.user]), request)
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




from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from edudream.modules.exceptions import raise_serializer_error_msg
from edudream.modules.paginations import CustomPagination
from edudream.modules.permissions import IsTutor, IsParent
from home.models import Profile, Transaction
from home.serializers import SignUpSerializerIn, LoginSerializerIn, UserSerializerOut, ProfileSerializerIn, \
    ChangePasswordSerializerIn, TransactionSerializerOut


class SignUpAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = SignUpSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response(response)


class LoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializerIn(data=request.data, context={"request": request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response({
            "detail": "Login Successful", "data": UserSerializerOut(user, context={"request": request}).data,
            "access_token": f"{RefreshToken.for_user(user)}"
        })


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated & (IsTutor | IsParent)]

    def get(self, request):
        return Response({"detail": "Success", "data": UserSerializerOut(request.user, context={"request": request}).data})

    def put(self, request):
        instance = get_object_or_404(Profile, user=request.user)
        serializer = ProfileSerializerIn(instance=instance, data=request.data, context={'request': request})
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        user = serializer.save()
        return Response({"detail": "Profile updated", "data": UserSerializerOut(user, context={"request": request}).data})


class ChangePasswordAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ChangePasswordSerializerIn(data=request.data)
        serializer.is_valid() or raise_serializer_error_msg(errors=serializer.errors)
        response = serializer.save()
        return Response({"detail": response})


class PaymentHistoryAPIView(APIView, CustomPagination):

    permission_classes = [IsAuthenticated & (IsTutor | IsParent)]

    def get(self, request, pk=None):
        trans_type = request.GET.get("type")
        amount_from = request.GET.get("amount_from")
        amount_to = request.GET.get("amount_to")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        status = request.GET.get("status")

        query = Q(user=request.user)

        if pk:
            queryset = get_object_or_404(Transaction, id=pk, user=request.user)
            serializer = TransactionSerializerOut(queryset).data
            return Response({"detail": "Success", "data": serializer})

        if amount_to and amount_from:
            query &= Q(amount__range=[amount_from, amount_to])

        if date_to and date_from:
            query &= Q(created_on__range=[date_from, date_to])

        if status:
            query &= Q(status=status)

        if trans_type:
            query &= Q(trasaction_type=trans_type)

        queryset = self.paginate_queryset(Transaction.objects.filter(), request)
        serializer = TransactionSerializerOut(queryset, many=True).data
        response = self.get_paginated_response(serializer).data
        return Response({"detail": "Success", "data": response})


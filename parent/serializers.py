from rest_framework import serializers
from django.contrib.auth.models import User

from edudream.modules.exceptions import InvalidRequestException
from django.contrib.auth.hashers import make_password

from student.models import Student


class ParentStudentSerializerOut(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.CharField(source="user.email")

    class Meta:
        model = Student
        exclude = []


class StudentSerializerIn(serializers.Serializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email_address = serializers.EmailField()
    password = serializers.CharField()
    dob = serializers.DateTimeField()
    grade = serializers.CharField()

    def create(self, validated_data):
        user = validated_data.get("user")
        password = validated_data.get("password")
        f_name = validated_data.get("first_name")
        l_name = validated_data.get("last_name")
        email = validated_data.get("email_address")
        d_o_b = validated_data.get("dob")
        grade = validated_data.get("grade")

        # Check if user with email exists
        if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise InvalidRequestException({"detail": "Email is taken"})

        # Create student user
        student_user = User.objects.create(
            first_name=f_name, last_name=l_name, email=email, username=email, password=make_password(password=password)
        )

        # Create student instance
        student = Student.objects.create(user=student_user, parent__user=user, dob=d_o_b, grade=grade)

        return ParentStudentSerializerOut(student, context={"request": self.context.get("request")}).data

    def update(self, instance, validated_data):
        instance.user.first_name = validated_data.get("first_name", instance.user.first_name)
        instance.user.last_name = validated_data.get("last_name", instance.user.last_name)
        instance.user.email = validated_data.get("email_address", instance.user.email)
        instance.dob = validated_data.get("dob", instance.dob)
        instance.grade = validated_data.get("grade", instance.grade)
        instance.user.save()
        instance.save()

        return ParentStudentSerializerOut(instance, context={"request": self.context.get("request")}).data

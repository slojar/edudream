import uuid
from threading import Thread

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from edudream.modules.GoogleAPI import generate_meeting_link
from edudream.modules.choices import ACCEPT_DECLINE_STATUS, DISPUTE_TYPE_CHOICES
from edudream.modules.email_template import tutor_class_creation_email, parent_class_creation_email, \
    tutor_class_approved_email, student_class_approved_email, student_class_declined_email
from edudream.modules.exceptions import InvalidRequestException
from edudream.modules.utils import get_site_details
from home.models import Subject, Transaction
from student.models import Student
from tutor.models import TutorDetail, Classroom, Dispute

class_grace_period = settings.CLASSROOM_GRACE_PERIOD


class TutorDetailSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = TutorDetail
        exclude = ["user"]


class ClassRoomSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        exclude = []


class CreateClassSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # Logged in student
    name = serializers.CharField()
    description = serializers.CharField()
    tutor_id = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    subject_id = serializers.IntegerField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        name = validated_data.get("name")
        description = validated_data.get("description")
        tutor_id = validated_data.get("tutor_id")
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        subject_id = validated_data.get("subject_id")

        tutor = get_object_or_404(TutorDetail, user__id=tutor_id)
        subject = get_object_or_404(Subject, id=subject_id)
        student = get_object_or_404(Student, user=user)
        tutor_user = tutor.user

        # Check Tutor availability
        if Classroom.objects.filter(start_date__gte=start_date, end_date__lte=end_date, status__in=["new", "accepted"]).exists():
            raise InvalidRequestException({"detail": "Period booked by another user, please select another period"})

        # Check parent balance is available for class amount
        balance = user.parent.wallet.balance
        if subject.amount > balance:
            raise InvalidRequestException({"detail": "Insufficient balance, please top-up wallet"})

        # Add grace period
        new_end_time = end_date + timezone.timedelta(minutes=int(class_grace_period))
        # Create class for student
        classroom = Classroom.objects.create(
            name=name, description=description, tutor=tutor_user, student=student, start_date=start_date,
            end_date=new_end_time, amount=subject.amount, subjects=subject
        )
        # Notify Tutor of created class
        Thread(target=tutor_class_creation_email, args=[classroom]).start()
        # Notify Parent of created class
        Thread(target=parent_class_creation_email, args=[classroom]).start()

        return ClassRoomSerializerOut(classroom, context={"request": self.context.get("request")}).data


class ApproveDeclineClassroomSerializerIn(serializers.Serializer):
    action = serializers.ChoiceField(choices=ACCEPT_DECLINE_STATUS)
    decline_reason = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        action = validated_data.get("action")
        decline_reason = validated_data.get("decline_reason")
        amount = instance.amount
        parent = instance.student.parent.user
        d_site = get_site_details()

        if action == "accept":
            # Generate meeting link
            meeting_id = str(uuid.uuid4())
            tutor_email = instance.tutor.email
            student_email = instance.student.user.email
            link = generate_meeting_link(
                meeting_name=f"{instance.name}", attending=[tutor_email, student_email], request_id=meeting_id,
                narration=instance.description, start_date=instance.start_date, end_date=instance.end_date
            )
            instance.status = "accepted"
            instance.meeting_link = link
            # Add amount to Escrow Balance
            d_site.escrow_balance += amount
            d_site.save()
            # Create transaction
            Transaction.objects.create(
                user=parent, trasaction_type="course_payment", amount=amount, narration=instance.description
            )
            # Send meeting link to student
            Thread(target=student_class_approved_email, args=[instance]).start()
            # Send notification to parent
            # Send meeting link to tutor
            Thread(target=tutor_class_approved_email, args=[instance]).start()
        elif action == "cancel":
            # Check if instance was initially in accepted state
            if not instance.status == "accepted":
                raise InvalidRequestException({"detail": "You can only cancel class request you recently accepted"})
            # Cancel class
            instance.status = "cancelled"
            # Subtract amount from Escrow Balance
            d_site.escrow_balance -= amount
            d_site.save()
            # Refund parent coin
            parent_wallet = parent.wallet
            parent_wallet.balance += amount
            parent_wallet.save()
            # Create refund transaction
            Transaction.objects.create(
                user=parent, trasaction_type="refund", amount=amount, narration=f"Refund, {instance.description}"
            )
            # Notify parent and student
            ...
        else:
            if not decline_reason:
                raise InvalidRequestException({"detail": "Kindly specify reason why you are declining this request"})
            # Update instance state
            instance.decline_reason = decline_reason
            instance.status = "declined"
            # Send notification to student
            Thread(target=student_class_declined_email, args=[instance]).start()
            # Send notification to parent
        instance.save()
        return ClassRoomSerializerOut(instance, context={"request": self.context.get("request")}).data


class DisputeSerializerOut(serializers.ModelSerializer):
    class Meta:
        model = Dispute
        exclude = []


class DisputeSerializerIn(serializers.Serializer):
    auth_user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    title = serializers.CharField(max_length=200, required=False)
    dispute_type = serializers.ChoiceField(choices=DISPUTE_TYPE_CHOICES)
    content = serializers.CharField()

    def create(self, validated_data):
        user = validated_data.get("auth_user")
        title = validated_data.get("title")
        d_type = validated_data.get("dispute_type")
        content = validated_data.get("content")

        if not title:
            raise InvalidRequestException({"detail": "Title is required"})

        # Create Dispute
        dispute, _ = Dispute.objects.get_or_create(submitted_by=user, title=title)
        dispute.dispute_type = d_type
        dispute.content = content
        dispute.save()
        return DisputeSerializerOut(dispute, context=self.context.get("request")).data

    def update(self, instance, validated_data):
        d_type = validated_data.get("dispute_type", instance.dispute_type)
        content = validated_data.get("content", instance.content)
        instance.dispute_type = d_type
        instance.content = content
        instance.save()
        return DisputeSerializerOut(instance, context=self.context.get("request")).data





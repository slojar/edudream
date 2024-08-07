from django.db import models
from django.contrib.auth.models import User

from edudream.modules.choices import DISPUTE_TYPE_CHOICES, DISPUTE_STATUS_CHOICES, CLASS_STATUS_CHOICES, \
    AVAILABILITY_STATUS_CHOICES, DAY_OF_THE_WEEK_CHOICES, PAYOUT_STATUS_CHOICES, CLASS_TYPE_CHOICES, \
    TUTOR_STATUS_CHOICES
from location.models import Country
from student.models import Student


class TutorDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    hobbies = models.CharField(max_length=200, default="")
    funfact = models.CharField(max_length=200, default="")
    linkedin = models.CharField(max_length=200, default="", blank=True, null=True)
    education_status = models.CharField(max_length=100, default="")
    university_name = models.CharField(max_length=150, blank=True, null=True)
    high_school_attended = models.CharField(max_length=200, blank=True, null=True)
    high_school_subject = models.CharField(max_length=150, blank=True, null=True)
    discipline = models.CharField(max_length=150, blank=True, null=True)
    diploma_type = models.CharField(max_length=100, default="")
    diploma_grade = models.CharField(max_length=100, default="", blank=True, null=True)
    diploma_file = models.FileField(upload_to="diploma-files", blank=True, null=True)
    proficiency_test_grade = models.CharField(max_length=100, default="", blank=True, null=True)
    proficiency_test_type = models.CharField(max_length=100, default="", blank=True, null=True)
    proficiency_test_file = models.FileField(upload_to="proficiency-test-files", blank=True, null=True)
    address_front_file = models.FileField(upload_to="address-files", blank=True, null=True)
    address_back_file = models.FileField(upload_to="address-files", blank=True, null=True)
    nationality_front_file = models.FileField(upload_to="nationality-files", blank=True, null=True)
    nationality_back_file = models.FileField(upload_to="nationality-files", blank=True, null=True)
    resume = models.FileField(upload_to="curriculum-vitaes", blank=True, null=True)
    status = models.CharField(max_length=50, choices=TUTOR_STATUS_CHOICES, default="pending")
    rest_period = models.IntegerField(default=10)
    subjects = models.ManyToManyField("home.Subject")
    max_student_required = models.IntegerField(default=10)
    updated_on = models.DateTimeField(auto_now=True)
    allow_intro_call = models.BooleanField(default=True)
    # max_hour_class_hour = models.IntegerField(default=120)

    def __str__(self):
        return f"{self.user.username}"


class Classroom(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True, null=True)
    tutor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # parent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="parent")
    student = models.ForeignKey(Student, related_name="class_student", on_delete=models.SET_NULL, blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    expected_duration = models.IntegerField(blank=True, null=True)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    status = models.CharField(max_length=50, choices=CLASS_STATUS_CHOICES, default="new")
    class_type = models.CharField(max_length=50, choices=CLASS_TYPE_CHOICES, default="normal")
    meeting_link = models.CharField(max_length=300, blank=True, null=True)
    meeting_id = models.CharField(max_length=300, blank=True, null=True)
    tutor_complete_check = models.BooleanField(default=False)
    student_complete_check = models.BooleanField(default=False)
    decline_reason = models.CharField(max_length=300, blank=True, null=True)
    subjects = models.ForeignKey("home.Subject", on_delete=models.SET_NULL, null=True, blank=True)
    pending_balance_paid = models.BooleanField(default=False)
    tutor_payment_expected = models.DateTimeField(blank=True, null=True)
    tutor_paid = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tutor.username}: {self.name} - {self.amount}"


class ClassDocument(models.Model):
    tutor = models.ForeignKey(User, on_delete=models.CASCADE)
    class_room = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    file = models.FileField(upload_to="subject-document")
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tutor.username}: {self.class_room.name}"


class StudentRating(models.Model):
    tutor = models.ForeignKey(User, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, blank=True, null=True, related_name="student")
    subject = models.ForeignKey("home.Subject", on_delete=models.SET_NULL, blank=True, null=True)
    rating = models.IntegerField(default=0)
    review = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} {}".format(self.tutor.username, self.student.user.username)


class Dispute(models.Model):
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    dispute_type = models.CharField(max_length=100, choices=DISPUTE_TYPE_CHOICES, default="payment")
    content = models.TextField()
    image = models.ImageField(upload_to="dispute-images", blank=True, null=True)
    status = models.CharField(max_length=100, choices=DISPUTE_STATUS_CHOICES, default="open")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.submitted_by.username}: {self.title}"


class TutorCalendar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    classroom = models.ManyToManyField(Classroom)
    day_of_the_week = models.CharField(max_length=200, choices=DAY_OF_THE_WEEK_CHOICES, default="mon")
    time_from = models.TimeField(blank=True, null=True)
    time_to = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=100, choices=AVAILABILITY_STATUS_CHOICES, default="available")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"


class TutorBankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_name = models.CharField(max_length=200)
    routing_number = models.CharField(max_length=300, blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_external_account_id = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"


class PayoutRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_account = models.ForeignKey(TutorBankAccount, on_delete=models.CASCADE)
    transaction = models.ForeignKey("home.Transaction", on_delete=models.SET_NULL, blank=True, null=True)
    coin = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    reference = models.CharField(max_length=300, blank=True, null=True)
    status = models.CharField(max_length=100, choices=PAYOUT_STATUS_CHOICES, default="pending")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: COIN - {self.coin}"


class TutorSubject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey("home.Subject", on_delete=models.CASCADE)
    tags = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}: {self.subject.name} - {self.subject.grade}"


class TutorSubjectDocument(models.Model):
    tutor_subject = models.ForeignKey(TutorSubject, on_delete=models.CASCADE)
    file = models.FileField(upload_to="tutor-subject-document")

    def __str__(self):
        return str(self.tutor_subject.subject.name)






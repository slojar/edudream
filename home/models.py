from django.contrib.sites.models import Site
from django.db import models
from django.contrib.auth.models import User

from edudream.modules.choices import TRANSACTION_TYPE_CHOICES, TRANSACTION_STATUS_CHOICES, ACCOUNT_TYPE_CHOICES
from location.models import City, State, Country


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=20)
    dob = models.DateTimeField(blank=True, null=True)
    address = models.CharField(max_length=300, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    account_type = models.CharField(max_length=100, choices=ACCOUNT_TYPE_CHOICES, default="tutor")
    email_verified = models.BooleanField(default=False)
    email_verified_code = models.CharField(max_length=200, blank=True, null=True)
    code_expiry = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=False)
    updated_on = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def email(self):
        return self.user.email

    def get_full_address(self):
        addr = ""
        if self.address:
            addr += f"{self.address}, "
        if self.city:
            addr += f"{self.city.name}, "
        if self.state:
            addr += f"{self.state.name}, "
        if self.country:
            addr += f"{self.country.name}, "
        return addr.strip()

    def __str__(self):
        return f"{self.user.username}"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    pending = models.DecimalField(decimal_places=2, max_digits=20, default=0)
    created_on = models.DateField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.user} - {self.balance}"


class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_digits = models.CharField(max_length=50)
    last_digits = models.CharField(max_length=50)
    card_type = models.CharField(max_length=50)
    expiry_date = models.CharField(max_length=50)
    card_token = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.card_type}"


class Notification(models.Model):
    user = models.ManyToManyField(User)
    message = models.CharField(max_length=500)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}"


class Subject(models.Model):
    name = models.CharField(max_length=200)
    grade = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    trasaction_type = models.CharField(max_length=60, choices=TRANSACTION_TYPE_CHOICES, default="fund_wallet")
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    status = models.CharField(max_length=50, choices=TRANSACTION_STATUS_CHOICES, default="pending")
    narration = models.CharField(max_length=200, blank=True, null=True)
    failed_reason = models.TextField()
    # payment_method = models.CharField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: amount - {self.amount}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")
    message = models.CharField(max_length=2000, blank=True, null=True)
    attachment = models.FileField(upload_to="chat-attachments", blank=True, null=True)
    read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sender: {self.sender.username} - Receiver: {self.receiver.username}"

    class Meta:
        ordering = ['created_on']


class PaymentPlan(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    coin = models.DecimalField(default=0, decimal_places=2, max_digits=20)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class SiteSetting(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    site_name = models.CharField(max_length=200, null=True, default="EduDream")
    google_calendar_id = models.CharField(max_length=300, blank=True, null=True)
    google_redirect_url = models.CharField(max_length=300, blank=True, null=True)
    coin_threshold = models.DecimalField(default=3, decimal_places=2, max_digits=20)
    class_grace_period = models.IntegerField(blank=True, null=True, default=0)
    enquiry_email = models.CharField(max_length=200, blank=True, null=True)
    escrow_balance = models.DecimalField(decimal_places=2, max_digits=20, default=0)

    def __str__(self):
        return self.site.name





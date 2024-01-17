from django.contrib import admin

from home.models import SiteSetting, PaymentPlan, Profile

admin.site.register(SiteSetting)
admin.site.register(PaymentPlan)
admin.site.register(Profile)
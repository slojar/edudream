from django.contrib import admin

from home.models import SiteSetting, PaymentPlan

admin.site.register(SiteSetting)
admin.site.register(PaymentPlan)

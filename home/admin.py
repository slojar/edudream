from django.contrib import admin

from home.models import SiteSetting, PaymentPlan, Profile, Language

admin.site.register(SiteSetting)
admin.site.register(PaymentPlan)
admin.site.register(Language)
admin.site.register(Profile)



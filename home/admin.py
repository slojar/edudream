from django.contrib import admin

from home.models import SiteSetting, PaymentPlan, Profile, Language, Subject, Testimonial, Notification

admin.site.register(SiteSetting)
admin.site.register(PaymentPlan)
admin.site.register(Language)
admin.site.register(Testimonial)
admin.site.register(Profile)
admin.site.register(Subject)
admin.site.register(Notification)



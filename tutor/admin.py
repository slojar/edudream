from django.contrib import admin

from tutor.models import TutorCalendar, Classroom, TutorBankAccount, PayoutRequest

admin.site.register(TutorCalendar)
admin.site.register(Classroom)
admin.site.register(TutorBankAccount)
admin.site.register(PayoutRequest)


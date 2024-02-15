from django.contrib import admin
from .models import *


class StateInline(admin.TabularInline):
    model = State
    extra = 0


class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    inlines = [
        StateInline
    ]


class StateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'country']
    search_fields = ['name', 'country__name']
    list_filter = ['country']


class CityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code']
    search_fields = ['name', 'state__name']
    list_filter = ['state__country']


admin.site.register(Country, CountryAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(City, CityAdmin)


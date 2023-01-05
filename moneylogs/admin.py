from django.contrib import admin
from .models import MoneyDayLog, MoneyCategory, MoneyDetailLog
# Register your models here.

admin.site.register(MoneyDayLog)
admin.site.register(MoneyDetailLog)
admin.site.register(MoneyCategory)
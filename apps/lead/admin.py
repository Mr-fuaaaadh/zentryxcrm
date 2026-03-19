from django.contrib import admin
from .models import Lead, LeadActivity, LeadManager
# Register your models here.


admin.site.register(Lead)
admin.site.register(LeadActivity)

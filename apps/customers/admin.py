from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):

    list_display = (
        "customer_code",
        "name",
        "email",
        "phone",
        "assigned_to",
        "is_active",
        "created_at",
    )

    search_fields = (
        "customer_code",
        "name",
        "email",
        "phone",
    )

    list_filter = (
        "customer_type",
        "assigned_to",
        "is_active",
    )

    readonly_fields = (
        "customer_code",
        "created_at",
        "updated_at",
    )

    list_per_page = 25
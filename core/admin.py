from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active")
    search_fields = ("email",)

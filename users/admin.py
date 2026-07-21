from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "created_at",
        "is_deleted",
    )

    search_fields = ["username", "email"]
    search_help_text = "Search by the username or email"


admin.site.register(User, UserAdmin)

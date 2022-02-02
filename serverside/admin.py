from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    BaseUserAdmin.list_display += ("has_dbuser",)

    list_filter = ("has_dbuser",)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for i, entry in enumerate(self.fieldsets):
            if entry[0] == "Permissions":
                self.fieldsets[i][1]["fields"] = (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "has_dbuser",
                    "groups",
                    "user_permissions",
                )
                break


admin.site.register(User, UserAdmin)

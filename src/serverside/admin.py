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

    def save_related(self, request, form, formsets, change):
        """
        Update database permissions

        Overwriting this method is necessary since the current permissions are not
        available in the model's save method, because m2m fields are set in
        ModelAdmin.save_related() afterwards.
        """
        super().save_related(request, form, formsets, change)
        form.instance.update_db_permissions()


admin.site.register(User, UserAdmin)

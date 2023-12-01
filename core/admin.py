from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ['phone', 'email', 'is_active']
    list_filter = ['is_active', 'is_superuser', 'is_staff']
    fieldsets = (
        (_('Personal info'), {'fields': ('phone', 'email', )}),
        (_('Permissions'), {'fields': ('is_active', 'is_superuser', 'is_staff', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ['phone', 'email']
    ordering = ['email']
    actions = ['active_users_accounts']
    list_editable = ['is_active']
    list_per_page = 15

    @admin.action(description="Active users accounts")
    def active_users_accounts(self, request, queryset):
        update_count = queryset.update(is_active=True)
        self.message_user(
            request,
            _(f"{update_count} of users account activated."),
            messages.SUCCESS
        )

    filter_horizontal = []
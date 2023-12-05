from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import CustomUser, OTP


# Custom Filter
class PasswordStatusFilter(admin.SimpleListFilter):
    title = 'password status'
    parameter_name = 'password'

    PASSWORD_EXPIRED = 'expired'
    PASSWORD_VALID = 'valid'

    def lookups(self, request, model_admin):
        return [
            (self.PASSWORD_EXPIRED, _('Expired')),
            (self.PASSWORD_VALID, _('Valid'))
        ]
    
    def queryset(self, request, queryset):
        if self.value() == self.PASSWORD_EXPIRED:
            return queryset.filter(expired_datetime__lt=timezone.now())
        elif self.value() == self.PASSWORD_VALID:
            return queryset.filter(expired_datetime__gte=timezone.now())


# Custom admin
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ['phone', 'email', 'is_active']
    list_filter = ['is_active', 'is_superuser', 'is_staff']
    fieldsets = (
        (_('Personal info'), {'fields': ('phone', 'email', 'password', )}),
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


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone', 'password', 'created_datetime', 'expired_datetime']
    list_filter = [PasswordStatusFilter]
    ordering = ['-created_datetime']

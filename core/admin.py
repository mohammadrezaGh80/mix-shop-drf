from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('phone', 'email', )
    list_filter = ('is_active', 'is_superuser', 'is_staff', )
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
    search_fields = ('email',)
    ordering = ('email',)

    filter_horizontal = []
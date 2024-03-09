from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect


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
    list_display = ['phone', 'email', 'is_active', 'is_staff']
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
    actions = ['active_users_accounts', 'add_user_to_staff', 'remove_users_from_staff']
    list_editable = ['is_active']
    readonly_fields = ['is_staff', 'is_superuser']
    filter_horizontal = []
    list_per_page = 15


    @admin.action(description='Active users accounts')
    def active_users_accounts(self, request, queryset):
        update_count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"حساب {update_count} نفر از کاربران فعال شد.",
            messages.SUCCESS
        )

    @admin.action(description='Add user to staff')
    def add_user_to_staff(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 
                              'دو یا چند کاربر را نمیتوانید به صورت همزمان ادمین کنید.',
                              messages.WARNING)
            return
        
        user = queryset.first()
        if not user.has_usable_password():
            self.message_user(request, 
                              f'کاربر(شماره تلفن: {user.phone}) رمز عبوری ندارد، لطفا یک رمز عبور برای کاربر وارد کنید.',
                              messages.WARNING)
            url = (
                reverse('admin:core_customuser_changelist')
                + f'{user.id}/password/'
            )
            return HttpResponseRedirect(url)
        
        user.is_staff = True
        user.save()

    @admin.action(description='Remove users from staff')
    def remove_users_from_staff(self, request, queryset):
        update_count = queryset.update(is_staff=False)
        self.message_user(request, 
                          f'{update_count} نفر از کاربران از ادمینی کنار گذاشته شدند.',
                          messages.SUCCESS)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone', 'password', 'created_datetime', 'expired_datetime']
    list_filter = [PasswordStatusFilter]
    ordering = ['-created_datetime']

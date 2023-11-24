from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .validators import PhoneValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, email=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given phone, email and password.
        """
        if not phone:
            raise ValueError(_('Users must have an phone number.'))
        
        if email:
            email = self.normalize_email(email)
        else:
            email = None

        user = self.model(
            phone=phone,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, email=None, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given phone, email and password.
        """
        user = self.create_user(
            phone=phone,
            email=email,
            password=password,
            **extra_fields
        )
        user.is_superuser = True
        user.is_active = True
        user.is_staff = True
        user.save(using=self._db)
        return user
    


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_validator = PhoneValidator()

    phone = models.CharField(max_length=11, unique=True, validators=[phone_validator], verbose_name=_("Phone"))
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name=_("Email"))

    is_active = models.BooleanField(
        default=False, verbose_name=_("Is active"),
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        )
    )
    is_staff = models.BooleanField(
        default=False, verbose_name=_("Is staff"), 
        help_text=_("Designates whether the user can log into this admin site.")
    )

    USERNAME_FIELD = "phone"

    objects = CustomUserManager()

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        
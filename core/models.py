from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from uuid import uuid4
import random
import string

from .validators import PhoneValidator
from .signals import superuser_created


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
        national_code = extra_fields.pop('national_code', None)
        user = self.create_user(
            phone=phone,
            email=email,
            password=password,
            **extra_fields
        )
        user.is_superuser = True
        superuser_created.send_robust(self.__class__, instance=user, national_code=national_code)
        user.is_staff = True
        user.save(using=self._db)
        return user
    


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_validator = PhoneValidator()

    phone = models.CharField(max_length=11, unique=True, validators=[phone_validator], verbose_name=_("Phone"))
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name=_("Email"))

    is_active = models.BooleanField(
        default=True, verbose_name=_("Is active"),
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        )
    )
    is_staff = models.BooleanField(
        default=False, verbose_name=_("Is staff"), 
        help_text=_("Designates whether the user can log into this admin site.")
    )

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "phone"

    objects = CustomUserManager()

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


# default value for expired datetime otp
def get_expired_datetime():
    return timezone.now() + timezone.timedelta(seconds=120)
        

class OTP(models.Model):
    phone_validator = PhoneValidator()

    id = models.UUIDField(primary_key=True, default=uuid4, verbose_name=_("Request id"))
    phone = models.CharField(max_length=11, validators=[phone_validator], verbose_name=_("Phone"))
    password = models.CharField(max_length=4, verbose_name=_("Password"))

    created_datetime = models.DateTimeField(default=timezone.now, verbose_name=_("Created datetime"))
    expired_datetime = models.DateTimeField(default=get_expired_datetime , verbose_name=_("Expired datetime"))

    def generate_password(self):
        self.password = self._random_password()

    def _random_password(self):
        rand = random.SystemRandom()
        return ''.join(rand.choices(string.digits, k=4))   
    
    def __str__(self):
        return f'{self.phone}: {self.password}'
    
    class Meta:
        verbose_name = _("One time password")
        verbose_name_plural = _("One time passwords")

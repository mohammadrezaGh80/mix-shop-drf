from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class PhoneValidator(RegexValidator):
    regex = r"^09[0-9]{9}$"
    message = _(
        'Enter a valid phone number, phone number must have 11 digits'
        ' which starts with the number 09.'
    )
    code = "invalid_phone"

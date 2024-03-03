from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class PhoneValidator(RegexValidator):
    regex = r"^09[0-9]{9}$"
    message = _(
        'Enter a valid phone number, phone number must have 11 digits'
        ' which starts with the number 09.'
    )
    code = "invalid_phone"

class NationalCodeValidator(RegexValidator):
    regex = r"^[1-9][0-9]{9}$"
    message = _(
        'Enter a valid national code, National code must be 10 digits'
        ' which start with one of the numbers between 1 and 9.'
    )
    code = "invalid_national_code"

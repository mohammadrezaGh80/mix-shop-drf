from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class PostalCodeValidator(RegexValidator):
    regex = r"^[0-9]{10}$"
    message = _(
        'Enter a valid postal code, Postal code must be 10 digits without dashes.'
    )
    code = "invalid_postal_code"


class NationalCodeValidator(RegexValidator):
    regex = r"^[1-9][0-9]{9}$"
    message = _(
        'Enter a valid national code, National code must be 10 digits'
        ' which start with one of the numbers between 1 and 9.'
    )
    code = "invalid_national_code"
    
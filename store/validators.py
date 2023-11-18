from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class PostalCodeValidator(RegexValidator):
    regex = r"^[0-9]{10}$"
    message = _(
        'Enter a valid postal code, Postal code must be 10 digits without dashes.'
    )
    code = "invalid_postal_code"
    
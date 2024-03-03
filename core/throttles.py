from rest_framework.throttling import AnonRateThrottle

import re


class RequestOTPThrottle(AnonRateThrottle):
    rate = '1/min'

    def allow_request(self, request, view):
        phone = request.data.get('phone', None)
        if not phone or (phone and re.search(r"^09[0-9]{9}$", phone) is None):
            return True
        
        return super().allow_request(request, view)

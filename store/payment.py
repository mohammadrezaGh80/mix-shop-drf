from django.conf import settings

import requests
import json

class ZarinpalSandbox:
    _zarinpal_request_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'
    _zarinpal_page_url = 'https://sandbox.zarinpal.com/pg/StartPay/'
    _zarinpal_verify_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'


    def __init__(self, merchant_id=settings.ZARINPAL_MERCHANT_ID):
        self.merchant_id = merchant_id

    def payment_request(self, rial_total_price, description, callback_url):
        request_header = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        request_data = {
            'MerchantID': self.merchant_id,
            'Amount': rial_total_price // 10,
            'Description': description,
            'CallbackURL': callback_url,
        }

        response = requests.post(url=self._zarinpal_request_url, data=json.dumps(request_data), headers=request_header)
        return response.json()
    
    def generate_payment_page_url(self, authority):
        return f'{self._zarinpal_page_url}{authority}'
    
    def payment_verify(self, rial_total_price, authority):
        request_header = {
            "accept": "application/json",
            "content-type": "application/json"
        }

        request_data = {
            'MerchantID': self.merchant_id,
            'Amount': rial_total_price // 10,
            'Authority': authority,
        }

        response = requests.post(url=self._zarinpal_verify_url, data=json.dumps(request_data), headers=request_header)
        return response.json()

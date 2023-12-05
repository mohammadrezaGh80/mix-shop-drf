from django.core.management import BaseCommand
from django.db import transaction

from core.models import OTP


class Command(BaseCommand):
    help = 'Delete all one-time password in database'

    @transaction.atomic
    def handle(self, *args, **options):
        print('Deleting all one-time passwords...')

        all_otp = OTP.objects.all()

        for otp in all_otp:
            otp.delete()

        print('Done.')

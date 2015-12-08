from django.core.management.base import BaseCommand, CommandError
from apps.subjects import utils

class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            utils.enroll_demo_subject()
        except:
            CommandError('Enroll of demo subject did not work.')

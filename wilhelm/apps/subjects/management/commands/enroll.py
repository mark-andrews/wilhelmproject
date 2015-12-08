import configobj
from django.core.management.base import BaseCommand, CommandError
from apps.subjects import utils

class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            for arg in args:
                subjects_bulk_enroll_file = configobj.ConfigObj(arg)
                utils.subject_enroll(subjects_bulk_enroll_file)
        except:
            CommandError('Enroll did not work.')

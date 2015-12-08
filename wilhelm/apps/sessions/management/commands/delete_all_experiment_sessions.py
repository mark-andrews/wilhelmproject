from django.core.management.base import BaseCommand, CommandError
from wilhelm.server import models
import wilhelm

class Command(BaseCommand):

    def handle(self, *args, **options):
        models.ExperimentSession.objects.all().delete()

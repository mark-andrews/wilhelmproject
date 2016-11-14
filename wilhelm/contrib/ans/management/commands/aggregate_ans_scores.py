from django.core.management.base import BaseCommand
from contrib.ans import models

class Command(BaseCommand):

    def handle(self, *args, **options):
        [x.save_aggregate_scores() for x in models.ANSPlaylist.objects.all()]

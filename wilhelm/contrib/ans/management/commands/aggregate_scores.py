from django.core.management.base import BaseCommand
from contrib.bartlett import models

class Command(BaseCommand):

    def handle(self, *args, **options):
        [x.save_aggregate_scores() for x in models.Playlist.objects.all()]
        [x.save_aggregate_scores() for x in models.PlaylistV2.objects.all()]

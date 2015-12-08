from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.archives.models import ExperimentRepository

#================================ End Imports ================================

class Command(BaseCommand):

    def handle(self, *args, **options):

        for repository in ExperimentRepository.objects.all():
            repository.make_archives()

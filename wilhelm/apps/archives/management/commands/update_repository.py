from __future__ import absolute_import

#=============================================================================
# Third party imports
#=============================================================================
import configobj

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.archives.utils import parse_repository
from apps.archives.models import ExperimentRepository
from apps.core.utils.django import update_or_create

#================================ End Imports ================================

class Command(BaseCommand):

    args = 'repository0.cfg repository1.cfg'
    help = 'Updates the repository information in archives app.'

    def handle(self, *args, **options):

        for arg in args:

            C = configobj.ConfigObj(arg)

            try:

                for repository_name, repository_details in C['repository'].items():

                    path, since, until, include, exclude\
                        = parse_repository(repository_details)

                    repository = update_or_create(
                        ExperimentRepository,
                        get_fields = {'name':repository_name},
                        update_fields = {'path':path,
                                         'since':since,
                                         'until':until}
                                     )

                    if include:
                        repository.set_included_commits(include)
                    
                    if exclude:
                        repository.set_excluded_commits(exclude)



            except KeyError:

                self.stderr.write('The cfg file should contain a [repository] entry.')
                raise

from __future__ import absolute_import

import os

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.archives.models import ExperimentRepository, ExperimentArchive

#================================ End Imports ================================

class Command(BaseCommand):

    help = """addexperiment [--hash d2h4c4g] [--remote foo.org:foo.git]  experiment_repository_name"""

    def add_arguments(self, parser):

        parser.add_argument('repository')

        parser.add_argument('--remote', 
            dest="remote_server", 
            required=False,
            help='The name of the remote public server for open access.'
            )


        parser.add_argument('--hash', 
            dest="commit_hash", 
            required=False,
            help='The name of the commit hash.'
            )

    def handle(self, *args, **options):

        repository_path = options['repository']
        commit_hash = options['commit_hash']
        remote_server = options['remote_server']

        assert os.path.exists(repository_path), 'Must exist'
        assert os.path.isdir(repository_path), 'Must be dir'

        repository = ExperimentRepository.new(repository_path)

        if remote_server:
            repository.remote_server = remote_server
            repository.save()

        if commit_hash:

            assert repository.has_commit(commit_hash),\
                """ Repository %s does not have commit hash "%s" """\
                % (repository.path, commit_hash)

            commit_hash, commit_date = repository.get_commit(commit_hash)
        else:
            commit_hash, commit_date = repository.get_head_commit()


        experiment_archive = ExperimentArchive.new(repository, commit_hash)


'''
Test the archives app.
'''

from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import datetime
import tempfile
import sh
import os
import shutil
import operator

#=============================================================================
# Third party package imports.
#=============================================================================
import configobj

#=============================================================================
# Django imports.
#=============================================================================
from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest

#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import conf, models, utils
from apps.testing import utils as testing_utils
from apps.testing import conf as testing_conf
from apps.archives import models as archives_models
from apps.archives import views
from apps.core.utils import sys, django

#================================ End Imports ================================

class ExperimentRepository(TestCase):

    def setUp(self):

        number_of_revisions = 10

        self.mock_repository_setup_dir\
            = testing_utils.make_mock_repository_files()

        self.mock_repository\
                = testing_utils.MockExperimentRepository(
                    setup_dir = self.mock_repository_setup_dir,
                    initial_date = datetime.datetime.now()
                )

        self.mock_repository.initialize()
        self.mock_repository.update(revisions=number_of_revisions)

        self.test_name = 'mock'
        self.test_description = 'A mock repository'

        self.setup_fields = dict(name = self.test_name, 
                                 description = self.test_description,
                                 date_created = datetime.datetime.now(),
                                 is_active = True, 
                                 path = self.mock_repository.path)

    def tearDown(self):
        shutil.rmtree(self.mock_repository.path)
        shutil.rmtree(self.mock_repository_setup_dir)

    def create_repository(self, set_includes_excludes=True):
        '''
        Create repository with included/excluded versions.
        '''

        experiment_repository = models.ExperimentRepository.objects\
                .create(**self.setup_fields)

        return experiment_repository

    def test_create(self):
        ''' Test if we are able to create the ExperimentRepository object.'''

        experiment_repository\
            = self.create_repository(set_includes_excludes=False)

        all_repositories = models.ExperimentRepository.objects.all()
        # Should have only 1 object.
        self.assertEqual(len(all_repositories), 1)
        
        # Check its name, path, branch, since, until, etc
        the_repository = all_repositories[0]
        self.assertEqual(experiment_repository, the_repository)
        self.assertEqual(the_repository.name, self.test_name)
        self.assertEqual(the_repository.path, self.mock_repository.path)
        self.assertEqual(the_repository.description,
                self.test_description)
        self.assertEqual(the_repository.branch, conf.default_git_branch)
        models.ExperimentRepository.objects.all().delete()

    def test_get_all_commits(self):
        '''
        Test if all the mock repository's commits match those in the repository
        listed in db.
        '''

        experiment_repository\
            = self.create_repository(set_includes_excludes=True)

        repository_all_commits\
        = experiment_repository.get_all_commits()

        mock_repository_all_commits\
                = self.mock_repository.get_all_commits()

        self.assertEqual(mock_repository_all_commits,
                repository_all_commits)

        # Delete the model.
        models.ExperimentRepository.objects.all().delete()


    def test_make_archives(self):
        '''
        Test that we can archive the repository versions (those listed in
        get_commits). 
        '''

        experiment_repository = self.create_repository()

        for commit_hash, commit_date in experiment_repository.get_all_commits():
            archives_models.ExperimentArchive.new(experiment_repository,
                                                  commit_hash)

        self.assertEqual(len(models.ExperimentRepository.objects.all()),
                         1)

        self.assertEqual(len(models.ExperimentArchive.objects.all()),
                         len(experiment_repository.get_all_commits()))


    def test_make_archives_repeat(self):
        '''
        Test that we can archive the repository versions (those listed in
        get_commits) when the make_archives command is run more than once.
        '''
        # Create the repository.
        experiment_repository = self.create_repository()

        for commit_hash, commit_date in experiment_repository.get_all_commits():
            archives_models.ExperimentArchive.new(experiment_repository,
                                                  commit_hash)

        self.assertEqual(len(models.ExperimentRepository.objects.all()),
                         1)

        self.assertEqual(len(models.ExperimentArchive.objects.all()),
                         len(experiment_repository.get_all_commits()))

        number_of_experiments = len(testing_conf.mock_experiment_names)

        self.assertEqual(len(models.ExperimentVersion.objects.all()),
                         number_of_experiments * len(experiment_repository.get_all_commits()))
        
        self.assertEqual(number_of_experiments, 
                         len(archives_models.Experiment.objects.all()))


        # And again.
        for commit_hash, commit_date in experiment_repository.get_all_commits():
            archives_models.ExperimentArchive.new(experiment_repository,
                                                  commit_hash)

        self.assertEqual(len(models.ExperimentRepository.objects.all()),
                         1)

        self.assertEqual(len(models.ExperimentArchive.objects.all()),
                         len(experiment_repository.get_all_commits()))
        
        for commit_hash, commit_date in experiment_repository.get_all_commits():
            archive = archives_models.ExperimentArchive.objects.get(commit_hash=commit_hash)

            self.assertEqual(archive.commit_hash, commit_hash)
            self.assertEqual(archive.commit_date, commit_date)

        number_of_experiments = len(testing_conf.mock_experiment_names)

        self.assertEqual(len(models.ExperimentVersion.objects.all()),
                         number_of_experiments * len(experiment_repository.get_all_commits()))
        
        self.assertEqual(number_of_experiments, 
                         len(archives_models.Experiment.objects.all()))

        commits = experiment_repository.get_all_commits()
        for archives in archives_models.ExperimentArchive.objects.all():
            self.assertIn(
                (archive.commit_hash, archive.commit_date), commits
            )

    
    def test_git_export(self):
        '''
        Test if we can succesfully export all versions of a git repository.
        '''

        mock_repository_all_commits\
                = self.mock_repository.get_all_commits()

        export_directories = {}
        for _hash, tstamp in mock_repository_all_commits:
            export_directories[_hash]\
                    = utils.git_export(self.mock_repository.path, _hash)

        for _hash, export_directory in export_directories.items():
            checksum_list = self.mock_repository.commit_dictionary[_hash]
            self.assertTrue(
                    sys.check_directory_checksums(
                        checksum_list, export_directory
                        )
                    )
            # Delete the exported directory.
            shutil.rmtree(export_directory)

    def test_make_tarball(self):
        '''
        Can we make tarballs for all versions in the git repository.
        '''        
        
        experiment_repository\
                = models.ExperimentRepository.objects.create(**self.setup_fields)

        for _hash, tstamp in experiment_repository.get_all_commits():
            experiment_details, tarball_path\
                    = utils.make_tarball(experiment_repository.path, _hash)

            ########
            # Test #
            ########

            # Do the experiment details look right?
            # Are the experiments mentioned in the settings file in the
            # experiment_details dir?
            experiments_settings = configobj.ConfigObj(os.path.join(
                            experiment_repository.path, 
                            conf.repository_settings_filename))

            for class_name in experiments_settings['experiments']:
                self.assertTrue(experiment_details.has_key(class_name))

            ########
            # Test #
            ########

            # Are the contents of the tarball as they should be?
            tmpdir = tempfile.mkdtemp()

            if conf.tarball_compression_method == 'bz2':
                tar_cmd = '-xjf'
            elif conf.tarball_compression_method == 'gz':
                tar_cmd = '-xzf'
 
            sh.tar(tar_cmd, tarball_path, '-C', tmpdir)

            checksum_list = self.mock_repository.commit_dictionary[_hash]
            self.assertTrue(
                    sys.check_directory_checksums(
                        checksum_list, tmpdir)
                    )

            # Delete the exported directory.
            shutil.rmtree(tmpdir)

            ########
            # Test #
            ########

            # Check the contents of the tarball; does it import.
            tarball_model = utils.ExperimentArchiveTarball(tarball_path)
            self.assertTrue(tarball_model.integrity_check())
            self.assertTrue(tarball_model.import_check())

            # Delete the tarball
            os.unlink(tarball_path)

        models.ExperimentRepository.objects.all().delete()

    def _test_experiment_current_version(self):
        '''
        Test if the set_current_version manager method for Experiments will
        create default current versions.
        '''
        experiment_repository = self.create_repository()
        # Make the archives.
        experiment_repository.make_archives()

        experiments_to_be_set\
            = models.Experiment.objects.set_default_current_version()

        commits = experiment_repository.get_commits()
        commits = sorted(commits, key=operator.itemgetter(1))
        most_recent_version = commits[-1][1]

        # The current version should be the most recent commit revision (for
        # all those experiments that were originally None).
        for experiment in experiments_to_be_set:
            self.assertEqual(experiment.current_version.archive.commit_date,
                                most_recent_version)
        
class UpdateOrCreate(TestCase):
    ''' 
    Test the update_or_create utils function.
    '''

    def test_create(self):
        '''
        Create an object with update_or_create.
        Check its attributes are correct.
        '''

        get_fields = dict(
            name = 'foo',
            description = 'A description',
            path = '/foo/bar'
            )

        repo = django.update_or_create(models.ExperimentRepository,
            get_fields = get_fields
            )

        # It should have the attributes in get_fields.
        for attr in get_fields:
            self.assertEqual(getattr(repo, attr), get_fields[attr])
            
        # Clean up.
        repo.delete()

    def test_retrieve(self):
        '''
        Create an object with update_or_create.
        Check if subsequent call to update_or_create will retrieve it.
        '''
        get_fields = dict(
            name = 'foo',
            description = 'A description',
            path = '/foo/bar'
            )

        repo = django.update_or_create(models.ExperimentRepository,
            get_fields = get_fields
            )
            
        # We should *retrieve* the above object here.
        alt_repo = django.update_or_create(models.ExperimentRepository,
            get_fields = get_fields
            )

        self.assertEqual(alt_repo, repo)
        
        # Clean up.
        repo.delete()
        alt_repo.delete()

    def test_default(self):
        '''
        Test the default fields and not update fields are used in the creation
        of the object.
        '''

        get_fields = dict(
            name = 'foo',
            )

        default_fields = dict(
            is_active = True,
            description = 'A description',
            path = '/bar/foo'
            )

        update_fields = dict(
            is_active = False,
            path = 'foo/bar'
            )

        repo = django.update_or_create(models.ExperimentRepository,
            get_fields = get_fields,
            default_fields = default_fields,
            update_fields = update_fields
            )

        # Make a union of both dictionaries.
        get_and_default_fields = {}
        get_and_default_fields.update(get_fields)
        get_and_default_fields.update(default_fields)

        # It should have the attributes in get_fields and default_fields.
        for attr in get_and_default_fields:
            self.assertEqual(getattr(repo, attr), get_and_default_fields[attr])

        # It should not have the attributes in updates.
        for attr in update_fields:
            self.assertNotEqual(getattr(repo, attr), update_fields[attr])

    def test_update(self):
        '''
        Test if the update_fields and not default fields are used in a get.
        '''

        get_fields = dict(
            name = 'foo',
            )

        default_fields = dict(
            is_active = True,
            description = 'A description',
            path = '/bar/foo'
            )

        update_fields = dict(
            is_active = False,
            path = 'foo/bar'
            )

        repo = django.update_or_create(models.ExperimentRepository,
            get_fields = get_fields,
            default_fields = default_fields,
            update_fields = update_fields
            )

        # Now, we update repo.
        repo = django.update_or_create(models.ExperimentRepository,
            get_fields = get_fields,
            default_fields = default_fields,
            update_fields = update_fields
            )

        # It should have the attributes in updates fields.
        for attr in update_fields:
            self.assertEqual(getattr(repo, attr), update_fields[attr])
 

class ExperimentListing(TestCase):

    def setUp(self):

        # Make a mock git project.
        self.mock_repository_setup_dir\
            = testing_utils.make_mock_repository_files()

        self.mock_repository\
             = testing_utils.MockExperimentRepository(
                 setup_dir = self.mock_repository_setup_dir)

        self.mock_repository.initialize()
        self.number_of_revisions = 10
        self.mock_repository.update(revisions=self.number_of_revisions)

        # Make a repository, archives, etc for the experiments.
        setup_fields = dict(name = 'mock',
                            description = 'A mock repository',
                            date_created = datetime.datetime.now(),
                            is_active = True,
                            path = self.mock_repository.path)

        self.experiment_repository = archives_models.ExperimentRepository\
            .objects.create(**setup_fields)

        for commit_hash, commit_date in self.experiment_repository.get_all_commits():
            archives_models.ExperimentArchive.new(self.experiment_repository,
                                                  commit_hash)

        # Set current version to default.
        archives_models.Experiment.objects.set_default_current_version()

    def tearDown(self):
        shutil.rmtree(self.mock_repository.path)
        shutil.rmtree(self.mock_repository_setup_dir)

    def test_url_resolves(self):
        listing_response = resolve('/listing')
        self.assertEqual(listing_response.func, views.listing)

    def _test_response_returns_correct_html(self):
        request = HttpRequest()
        response = views.listing(request)
        self.assertTrue(response.content.startswith('<!DOCTYPE html>'))
        self.assertTrue(response.content.endswith('</html>\n'))

        for mock_experiments in testing_conf.mock_experiment_names:
            self.assertIn(mock_experiments.lower(), 
                          response.content)

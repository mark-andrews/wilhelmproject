'''
Test the sessions app.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import datetime
import shutil
from random import choice

#=============================================================================
# Django imports.
#=============================================================================
from django.test import TestCase

#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import models
from apps import testing
from apps.testing import utils as testing_utils
from apps.subjects import utils as subjects_utils
from apps.subjects import models as subjects_models
from apps.archives import models as archives_models

#================================ End Imports ================================

class ImportTest(TestCase):
    def setUp(self):

        # Make some mock subjects.
        subjects_utils.subject_enroll(testing.mock_subjects)

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
        self.experiment_repository.make_archives()

        # Set current version to default.
        archives_models.Experiment.objects.set_default_current_version()

    def tearDown(self):
        shutil.rmtree(self.mock_repository.path)
        shutil.rmtree(self.mock_repository_setup_dir)

    def test_make_experiment_session(self):
        '''
        Make an experiment session entry. Test if its attributes are as we
        would expect.
        '''
        experiment_name = 'Rusty'
        subject_name = choice(testing.mock_subjects.keys())
        # TODO (Tue 02 Dec 2014 23:27:11 GMT): What are we trying to do here?
        experiment = archives_models.Experiment.objects.get(
            class_name = experiment_name
        )
        subject = subjects_models.Subject.objects.get(user__username =
                                                      subject_name)

        session = models.ExperimentSession.new(subject, experiment_name)

        # Is the session an instance of an ExperimentSession.
        self.assertIsInstance(session, models.ExperimentSession)

        # Is `subject` the subject of the session.
        self.assertEqual(session.subject, subject)

        # Is the experiment version the current version.
        latest_version\
        = archives_models.ExperimentVersion.objects.filter(
            experiment__class_name=experiment_name)\
            .latest('archive__commit_date')

        self.assertEqual(session.experiment_version.label,
                         latest_version.label)

        # Attempts (for this new session) should be zero.
        self.assertEqual(session.attempt, 0)

        # Should have status 'status_initialized'.
        self.assertEqual(session.status,
                         models.ExperimentSession.status_initialized)

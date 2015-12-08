'''
A test of the presenter/model. Test if we can make a LiveExperimentSession
object.
'''
from __future__ import absolute_import

#============================================================================= 
# Standard library imports
#=============================================================================
import datetime
import logging
from random import choice

#=============================================================================
# Django imports.
#=============================================================================
from django.conf import settings
from django.test import TestCase 

#=============================================================================
# Wilhelm imports.
#=============================================================================
from .. import models
from apps import testing
#from apps.core.utils import strings
from apps.testing import utils as testing_utils
from apps.archives import models as archives_models
from apps.sessions import models as session_models
from apps.subjects import models as subjects_models
from apps.presenter import models as presenter_models
from apps.subjects import utils as subjects_utils
from apps.core.utils import django


#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

#=============================================================================
# TestCase Classes
#=============================================================================
class PresenterModels(TestCase):
    '''
    Test apps.presenter.models.
    '''

    def setUp(self):
        '''
        We will use the testing GenericSetup to create the mock
        ExperimentRepository, Experiment and ExperimentVersion models.

        In addition, we will create mock subjects, and then create a mock
        experiment session for an arbitrarily chosen mock subject and mock
        experiment. Finally, we create a live experiment session for this
        experiment session.

        '''

        self.generic_setup = testing_utils.GenericSetup()

        for attr in ('mock_repository', 'mock_repository_setup_dir'):
            setattr(self, attr, getattr(self.generic_setup, attr))

        subjects_utils.subject_enroll(testing.mock_subjects)

        # FIXME. How about randomly choosing a subject and experiment.
        self.subject_name = choice(testing.mock_subjects.keys())
        self.subject = subjects_models.Subject.objects.get(
            user__username = self.subject_name)

        self.experiment_name = 'Rusty'
        self.experiment = archives_models.Experiment.objects.get(
            class_name = self.experiment_name
        )

        experiment_session\
            = session_models.ExperimentSession.new(self.subject, 
                                                   self.experiment_name)

        self.experiment_session_uid = experiment_session.uid

        live_session = presenter_models.LiveExperimentSession.new(
                experiment_session)
        self.live_session_uid = live_session.uid

    def test_new_live_experiment_session(self):
        '''
        Test that the live experiment session we created has all the properties
        it ought to have.
        '''

        self.assertEqual(len(models.LiveExperimentSession.objects.all()), 
                         1)

        self.assertEqual(len(session_models.ExperimentSession.objects.all()), 
                         1)

        live_session = models.LiveExperimentSession.objects.get(
                uid=self.live_session_uid)

        self.assertIsInstance(live_session, models.LiveExperimentSession)

        experiment_session = session_models.ExperimentSession.objects.get(
                uid=self.experiment_session_uid)

        self.assertIsInstance(experiment_session, 
                              session_models.ExperimentSession)

        self.assertEqual(live_session.experiment_session,
                         experiment_session)

        self.assertNotEqual(live_session.uid, None)
        self.assertEqual(len(live_session.uid), settings.UID_LENGTH)
        self.assertEqual(live_session.uid, live_session.pk)
        self.assertTrue(live_session.keep_alive)
        self.assertFalse(live_session.is_nowplaying)
        self.assertEqual(live_session.nowplaying_ping_uid, None)
        self.assertEqual(live_session.last_activity, None)
        self.assertEqual(live_session.last_ping, None)
        self.assertIsNot(live_session.date_created, None)


    def test_LiveExperimentSessionManager_methods(self):
        '''
        Test the get_live_sessions and is_some_session_live methods of the
        LiveExperimentSessionManager.
        '''

        live_session = models.LiveExperimentSession.objects.get(
                uid=self.live_session_uid)

        live_sessions\
            = models.LiveExperimentSession.objects.get_live_sessions(
                self.subject
            )

        self.assertEqual(len(live_sessions), 1)

        self.assertEqual(live_sessions[0], live_session)

        self.assertTrue(models.LiveExperimentSession\
                        .objects.is_some_session_live(self.subject),
                        True)

    def test_stamp_time(self):
        '''
        Test the stamp_time method and last_activity attribute of
        LiveExperimentSession model.
        '''

        now = datetime.datetime.now()

        live_session = models.LiveExperimentSession.objects.get(
                uid=self.live_session_uid)

        live_session.stamp_time()

        experiment_session = session_models.ExperimentSession.objects.get(
                uid=live_session.experiment_session.uid)


        self.assertEqual(live_session.last_activity,
                         experiment_session.last_activity)

        # Here, we are seeing if the last_activity is *more or less* now.
        live_session.stamp_time()
        now = datetime.datetime.now()
        self.assertAlmostEqual(
            (live_session.last_activity - now).total_seconds(),
            0, places=1)

    def test_keep_alive(self):
        '''
        Test the set_keep_alive method and keep_alive attribute of the
        LiveExperimentSession model.
        '''

        live_session = models.LiveExperimentSession.objects.get(
                uid=self.live_session_uid)

        live_session.set_keep_alive()
        self.assertTrue(live_session.keep_alive)

    def test_iterate_playlist_and_hangup(self):

        live_session = models.LiveExperimentSession.objects.get(
                uid=self.live_session_uid)

        self.assertEqual(live_session.nowplaying_ping_uid, None)
        self.assertFalse(live_session.is_nowplaying)

        ping_uid = django.uid()

        session_slide = live_session.iterate_playlist(ping_uid)

        self.assertEqual(live_session.nowplaying_ping_uid, ping_uid)
        self.assertTrue(live_session.is_nowplaying)

        self.assertEqual(session_slide.ping_uid, ping_uid)

        live_session.hangup_nowplaying()

        self.assertEqual(live_session.nowplaying_ping_uid, None)
        self.assertFalse(live_session.is_nowplaying)

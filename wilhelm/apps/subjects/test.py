from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
from random import choice

#=============================================================================
# Django imports
#=============================================================================
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps import testing
from apps.testing.utils import enroll_mock_subjects
from .models import Subject
from . import utils, models, conf

#================================ End Imports ================================

number_of_temp_subjects = 10

class SubjectEnroll(TestCase):

    def setUp(self):
        utils.subject_enroll(testing.mock_subjects)
        self.number_of_subjects = len(testing.mock_subjects)

    def tearDown(self):
        pass

    def test_enrollment(self):
        '''
        Using the mock_subjects.cfg in testing/, there should be two subjects
        enrolled and two users made.
        Check that the two subjects's user fields point to the users.
        '''
        self.assertEqual(len(models.Subject.objects.all()), self.number_of_subjects)
        self.assertEqual(len(User.objects.all()), self.number_of_subjects)

        for name in testing.mock_subjects.keys():
            subject = models.Subject.objects.get(user__username = name)
            user = User.objects.get(username=name)
            self.assertEqual(user, subject.user)

class tempSubjects(TestCase):
    '''
    Test if we are able to create some temp subjects.
    '''

    def setUp(self):

        mock_subjects = enroll_mock_subjects()
        self.n_mock_subjects = len(mock_subjects)

        self._user, _subject = choice(mock_subjects)

        self.temp_subjects = []
        for _ in xrange(number_of_temp_subjects):
            self.temp_subjects.append(
                models.Subject.objects.create_temp_subject(self._user)
            )

    def test_temp_subject(self):

        all_subjects = models.Subject.objects.all()
        all_users = models.User.objects.all()

        self.assertEqual(len(all_subjects),
                         self.n_mock_subjects + number_of_temp_subjects)

        self.assertEqual(len(all_users),
                             self.n_mock_subjects)

        for temp_subject in self.temp_subjects:
            self.assertEqual(self._user, 
                             temp_subject.user)

class demoSubject(TestCase):

    def setUp(self):

        self.user = utils.enroll_demo_subject()

        self.factory = RequestFactory()

    def test_demo_subject_enroll(self):

        user = User.objects.get(username = conf.demo_username)
        self.assertTrue(user)

        self.assertEqual(user, self.user)

    def test_demo_subject_login(self):

        self.assertTrue(
            self.client.login(username = conf.demo_username,
                              password = conf.demo_user_password)
        )

        self.assertIn('_auth_user_id', self.client.session)

        self.assertEqual(int(self.client.session['_auth_user_id']), 
                         self.user.pk)

    def create_temp_subject(self):
        subject = Subject.objects.create_temp_subject(self.user)

        self.assertEqual(subject.user, self.user)

        self.assertEqual(Subject.objects.filter(user = self.user), 1)

        self.assertTrue(subject.temp_subject)


    def test_demo_subject_wilhelmlogin(self):

        pass


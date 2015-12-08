'''
A test of the presenter/model. Test if we can make a LiveExperimentSession
object.
'''
from __future__ import absolute_import

#============================================================================= 
# Standard library imports
#=============================================================================
from random import choice
import json
import logging

#=============================================================================
# Django imports.
#=============================================================================
from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.conf import settings
#from django.utils.importlib import import_module
from importlib import import_module
from django.core.urlresolvers import resolve
from django.test import TestCase, Client
from django.http import HttpRequest

#=============================================================================
# Wilhelm imports.
#=============================================================================
from .. import models, views, conf
from ..utils.slideviews import get_slide_to_be_launched_info
from apps.testing import conf as testing_conf
from apps.testing import utils as testing_utils
from apps.sessions import models as session_models
from apps.sessions import conf as sessions_conf
from apps.front.conf import login_url
from apps.core.utils.django import (push_redirection_url_stack,
                                    http_redirect)

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

#=============================================================================
# Helper functions.
#=============================================================================
def user_login(username, password):
    client = Client()
    logged_in_user = client.login(username=username, password=password)
    assert logged_in_user, 'A user should be logged in.'
    
def new_client(SessionStore):

    '''
    Make a new test client object with a session store. Supply a SessionStore.
    '''

    client = Client()

    store = SessionStore()
    store.save()

    client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

    return client

def anon_request(SessionStore):
    '''
    Make a new request object with an anonymous user and a session. Supply a
    SessionStore.
    '''

    request = HttpRequest()
    request.session = SessionStore()
    request.session.save()

    user = get_user(request)
    request.user = user
    assert request.user.is_anonymous(), 'The request.user should be anonymous.'

    return request

def set_client_session_variable(client, key, value):

    '''
    This is a work around to set the value of test client session variable,
    see https://code.djangoproject.com/ticket/10899
    '''

    s = client.session
    s[key] = value
    s.save()


#=============================================================================
# TestCase Classes
#=============================================================================
class SlideLauncherSlideView(TestCase):
    '''
    Test the SlideLauncher and SlideView. Given that this are so
    inter-dependent, it not possible to test them independently.
    '''
    def setUp(self):
        '''
        We'll use the generic testing setup, we also need a session engine.
        The generic testing setup gives up 3 slides.

        '''

        self.generic_setup = testing_utils.GenericSetup()
        self.mock_users = testing_utils.get_mock_users()
        self.mock_subjects = testing_utils.enroll_mock_subjects()

        # TODO. This could go into the GenericSetup.
        self.experiment_names = map(str.lower,
                                    testing_conf.mock_experiment_names)

        self.engine = import_module(settings.SESSION_ENGINE)

    #=========================================================================
    # Helper (non-test) functions
    #=========================================================================
    def _make_request(self):

        username, password = choice(self.mock_users)
        request = self._new_request(username, password)
        experiment_name = choice(self.experiment_names)

        return experiment_name, request

    def _new_request(self, username, password):

        request = HttpRequest()
        request.session = self.engine.SessionStore()
        request.session.save()

        user_login(username, password)

        user = User.objects.get(username = username)

        request.user = user

        return request
 
    def _slide_launcher(self, experiment_name, request):
        '''
        A convenience function to call the slide launcher for experiment
        `experiment_name`. If a new request is required, it is returned for use
        in subsequent functions.
        '''

        views.experiment_launcher(request, experiment_name)

        return request

    def _slide_view(self, experiment_name, request):
        '''
        A convenience function to call a slide view for experiment
        `experiment_name`. It assumes that the launcher for that experiment has
        been called, and so the key to the SlideToBeLaunched model is in the
        request session.
        '''

        slide_to_be_launched_info = get_slide_to_be_launched_info(request)

        views.experiment(request, 
                         experiment_name,
                         slide_to_be_launched_info.ping_uid_short)


    def _slide_hangup(self, experiment_name, request, client=None):
        '''
        A convenience function to call the slide hangup. If a new client is
        made, it is and returned for use in subsequent functions.
        '''

        if client is None:
            client = self._new_client(request)

        slide_to_be_launched_info = get_slide_to_be_launched_info(request)

        post_url = '/hangup_nowplaying'
        post_data = {'is_hangup': json.dumps(True),
                     'ping_uid': slide_to_be_launched_info.ping_uid}
        self._post_json(client, post_url, post_data)

        return client

    def _pause_playlist(self, client):
        '''
        A convenience function to hangup a playlist. This assumes that a slide
        launcher has just been called.
        '''

        post_url = '/hangup_playlist'
        post_data = {'next_playlist_action': 'pause_playlist'}
        self._post_json(client, post_url, post_data)

        return client    
    
    def _new_client(self, request):
        ''' Make a client with the live_experiment as one of its
        session variables. '''
        client = new_client(self.engine.SessionStore)
        set_client_session_variable(client,
                                conf.live_experiment,
                                request.session[conf.live_experiment])
        return client

    def _post_json(self, client, post_url, post_data):
        ''' Send a json based post request to post_url.'''

        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        return client.post(post_url, post_data, **kwargs)

    #=========================================================================
    # Helper testing functions
    #=========================================================================
    def _test_slide_launcher(self, 
                             request,
                             experiment_name, 
                             slideview_type,
                             response_contents):
        '''
        A generic test of whether the slide launcher works.

        - Does the url resolve to the launcher?
        - Does the launcher return an expected response?
        - Does the session variable have a slide_to_be_launched object with the
        right properties?

        '''

        found = resolve('/' + experiment_name)
        self.assertEqual(found.func, views.try_experiment_launcher)

        response = views.try_experiment_launcher(request, experiment_name)

        self.assertTrue(response.content.startswith('<!DOCTYPE html>'))
        self.assertTrue(response.content.endswith('</html>\n'))

        self.assertTrue(
            request.session.get('slide_to_be_launched_info_uid', False)
        )

        slide_to_be_launched_info = get_slide_to_be_launched_info(request)

        for attr in conf.slide_to_be_launched_attrs:
            self.assertTrue(
                hasattr(slide_to_be_launched_info, attr),
                        msg = 'Attr %s was missing.' % attr
            )

        self.assertTrue(
            slide_to_be_launched_info.slideview_type == slideview_type,
            msg = 'Slideview type is %s.' % slide_to_be_launched_info.slideview_type
        )

        response_contents.append('window.location.href = "/%s/%s"' %
                                 (experiment_name,
                                  slide_to_be_launched_info.ping_uid_short))


        for response_content in response_contents:
            self.assertIn(response_content, response.content)            

    def _test_slide_view(self, request, experiment_name):
        '''
        A generic test of whether a slide view works. This tests assumes that a
        launcher for the relevant experiment has just been called.
        '''

        slide_to_be_launched_info = get_slide_to_be_launched_info(request)

        experiment_url\
            = '/'.join([experiment_name, slide_to_be_launched_info.ping_uid_short])

        found = resolve('/'+experiment_url)

        self.assertEqual(found.func, views.try_experiment)

        response = views.try_experiment(request, 
                                    experiment_name, 
                                    slide_to_be_launched_info.ping_uid_short)

        self.assertTrue(response.content.startswith('<!DOCTYPE html>'))
        self.assertTrue(response.content.endswith('</html>\n'))

        self.assertTrue(request.session.has_key(conf.live_experiment))

        live_session = models.LiveExperimentSession.objects.get(
            pk = request.session[conf.live_experiment]
        )

        self.assertTrue(hasattr(live_session, 'nowplaying_ping_uid'))
        self.assertNotEqual(live_session.nowplaying_ping_uid, None)
        self.assertEqual(live_session.nowplaying_ping_uid, 
                         slide_to_be_launched_info.ping_uid)

    def _test_slide_hangup(self, request, client):
        '''
        Assuming a slide has just been returned and thus there is a live
        session, this tests that the slide hangup works.
        '''

        post_url = '/hangup_nowplaying'
        found = resolve(post_url)
        self.assertEqual(found.func, views.hangup_nowplaying_gateway)


        slide_to_be_launched = get_slide_to_be_launched_info(request)

        post_data = {'is_hangup': json.dumps(True),
                     'ping_uid': slide_to_be_launched.ping_uid}

        response = self._post_json(client, post_url, post_data)
        json_response = json.loads(response.content)

        self.assertIs(type(json_response), dict)
        self.assertTrue(json_response.has_key('is_hangup'))
        self.assertTrue(json_response['is_hangup'])

        live_session = models.LiveExperimentSession.objects.get(
            uid = request.session[conf.live_experiment]
        )

        self.assertFalse(live_session.is_nowplaying)
        self.assertIs(live_session.nowplaying_ping_uid, None)

    def _test_pause_playlist(self, request, client):
        '''
        Test the pausing of a playlist. We assume that we have just been
        returned a LivePlaylist slide launcher, which will give the option of
        pausing or continuing.

         - Can we resolve the hangup_playlist url?
         - Do we get the right json handshake?
         - Is the session variable pointing to the live_session None-ified?
         - Is the live_session deleted?
         - Is the experiment_session status=paused?
        '''


        # Save these for comparison later.  
        live_experiment_pk = request.session[conf.live_experiment]
        live_session = models.LiveExperimentSession.objects.get(
            pk = live_experiment_pk
        )
        experiment_session_pk = live_session.experiment_session.pk
        ################################################################
        
        post_url = '/hangup_playlist'
        found = resolve(post_url)
        self.assertEqual(found.func, views.hangup_playlist_gateway)

        post_data = {'next_playlist_action': 'pause_playlist'}
    
        response = self._post_json(client, post_url, post_data)

        json_response = json.loads(response.content)

        self.assertIs(type(json_response), dict)
        self.assertTrue(json_response.has_key('next_uri'))
        self.assertTrue(json_response['next_uri'] == conf.default_url)


        live_session = models.LiveExperimentSession.objects.filter(
            pk = live_experiment_pk, alive = True
        )

        experiment_session\
            = session_models.ExperimentSession.objects.get(
            pk = experiment_session_pk
        )

        self.assertFalse(client.session.has_key(conf.live_experiment))
        self.assertEqual(len(live_session), 0)
        self.assertEqual(experiment_session.status,
                            sessions_conf.status_paused)    



    #=========================================================================
    # Test functions
    #=========================================================================
    
    #=========================================================================
    # Anonymous views
    #=========================================================================
    def test_anonymous_slide_launcher(self):
        '''
        If you request an experiment page, you will be redirected.
        '''

        for experiment_name in self.experiment_names:
            response = self.client.get('/' + experiment_name)
            self.assertRedirects(response, login_url)

    #=========================================================================
    # InitialPlaylist SlideLauncher, SlideView, Hangup tests
    #=========================================================================
    def test_initial_playlist_slide_launcher(self):
        '''
        Test that an *initial playlist slide launcher* is received when an
        anonymous user request an experiment for the first time.
        Also, see if the request.session[slide_to_be_launched] exists and has
        all the correct information to launch the slide.
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        ################################################################

        response_contents\
            = ['You are about to start experiment "%s".' % experiment_name]

        self._test_slide_launcher(
            request, 
            experiment_name,
            conf.slideview.InitialPlaylistSlideView,
            response_contents)

    def test_initial_playlist_slide_view(self):
        '''
        After we call the launcher, then everything should be ready to get the
        right view.

        Does the url resolve correctly? Does the response have the expected
        content? Do we create new live sessions?
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        ################################################################

        self._test_slide_view(request, experiment_name)

    def test_initial_playlist_slide_hangup(self):
        '''
        After we get the slide from an initial playlist, can we successfully
        hangup this slide?
        Does the url for nowplaying slide resolve? Are we returned the correct
        json object with the correct value, i.e. is_hangup = True.
        The live_session should also hangup, None-ifying the nowplayingfile and
        ping_uid and setting is_nowplaying to false.
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        ################################################################

        # We want to perform an ajax post so that's why we use client.
        client = self._new_client(request)

        self._test_slide_hangup(request, client)

    #=========================================================================
    # LivePlaylist SlideLauncher, SlideView, Hangup tests
    #=========================================================================
    def test_live_playlist_slide_launcher(self):
        '''
        After we sucessfully hangup an initial playlist slide, and then
        recontact the experiment url, do we get a LivePlaylistSlideView?
        Does the experiment url still resolve?
        Do we get a LivePlaylistSlideView?
        Do we have a href to the real experiment?
        Do we have the right messages in the render launcher template?
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        self._slide_hangup(experiment_name, request)
        ################################################################

        response_contents = []

        response_contents.append(
            'You have finished Part 1 of the experiment "%s".'
            % experiment_name)

        response_contents.append('There are 2 parts remaining.')

        response_contents.append(
            'To continue the experiment now, you can press the "%s" button.'
            % conf.button.next)

        response_contents.append(
            'To continue later, you can press the "%s" button.'
            % conf.button.pause)

        self._test_slide_launcher(request,
                                  experiment_name,
                                  conf.slideview.LivePlaylistSlideView,
                                  response_contents)

    def test_live_playlist_slide_view(self):
        '''
        After we call the LivePlaylistSlideLauncher, can we succesfully get the
        next slide.

        When dealing with LivePlaylist slides, we should not be creating new
        LiveExperimentSessions.
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        self._slide_hangup(experiment_name, request)
        self._slide_launcher(experiment_name, request)
        ################################################################

        self._test_slide_view(request, experiment_name)

    def test_live_playlist_slide_hangup(self):
        '''
        Can we hangup a live_playlist slide?
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        self._slide_hangup(experiment_name, request)
        self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        ################################################################

        client = self._new_client(request)
        self._test_slide_hangup(request, client)

    #=========================================================================
    # Pause and resume playlist.
    #=========================================================================
    def test_pause_playlist_after_1_slide(self):
        '''
        When we get the LivePlaylist slide launcher, we get an option to pause
        or continue. Can we pause?

        In this version, we assume we have gotten and hanged-up just the
        initial slide.

        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        client = self._slide_hangup(experiment_name, request)
        self._slide_launcher(experiment_name, request)
        ################################################################

        self._test_pause_playlist(request, client)

    def test_pause_playlist_after_2_slides(self):
        '''
        When we get the LivePlaylist slide launcher, we get an option to pause
        or continue. Can we pause?

        In this version, we assume we have gotten and hanged-up an initial
        slide and then gotten and hanged up a second slide. 

        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()
        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        client = self._slide_hangup(experiment_name, request)
        self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        self._slide_hangup(experiment_name, request, client)
        self._slide_launcher(experiment_name, request)
        ################################################################

        self._test_pause_playlist(request, client)

    def test_resume_paused_playlist(self):
        '''
        Test of PausedPlaylist SlideLauncher.
        '''

        ################################################################
        # Necessary setup for this test.
        experiment_name, request = self._make_request()

        request = self._slide_launcher(experiment_name, request)
        self._slide_view(experiment_name, request)
        client = self._slide_hangup(experiment_name, request)

        request = self._slide_launcher(experiment_name, request)
        client = self._pause_playlist(client)
        ################################################################

        # Copy the client's session to the request session.
        request.session = client.session 

        response_contents\
            = ['You are about to resume experiment "%s"' % experiment_name]

        self._test_slide_launcher(
            request, 
            experiment_name,
            conf.slideview.PausedPlaylistSlideView,
            response_contents)


class RedirectionStackTestCase(TestCase):

    def setUp(self):

        self.engine = import_module(settings.SESSION_ENGINE)
        self.request = self.new_request()
        self.test_urls = ['foo', 'bar', 'foobar', 'barfoo']

    def new_request(self):

        request = HttpRequest()
        request.session = self.engine.SessionStore()
        request.session.save()

        return request

    def test_redirection_url_stack(self):

        self.assertFalse('redirection_url_stack' in self.request.session)

        for url in self.test_urls:

            push_redirection_url_stack(self.request, url)

            self.assertIn(url, 
                          self.request.session['redirection_url_stack'])

        self.assertTrue('redirection_url_stack' in self.request.session)

        i = 0
        for test_url in self.test_urls[::-1]:

            i += 1

            redirection_url = http_redirect(self.request)

            self.assertEqual(redirection_url.url, test_url)

            self.assertNotIn(test_url,
                             self.request.session['redirection_url_stack'])

            self.assertEqual(len(self.request.session['redirection_url_stack']),
                             len(self.test_urls) - i)

        self.assertEqual(len(self.request.session['redirection_url_stack']), 
                         0)

        self.assertEqual('/', http_redirect(self.request).url)
        self.assertEqual('/', http_redirect(self.request).url)

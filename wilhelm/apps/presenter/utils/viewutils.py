from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging

#=============================================================================
# Third part imports
#=============================================================================
from ipware.ip import get_real_ip

#=============================================================================
# Django imports.
#=============================================================================
from django.contrib.gis.geoip import GeoIP
from django.shortcuts import redirect

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core.utils.django import http_response, push_redirection_url_stack
from .. import models, conf
from apps.front.conf import login_url

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

def presenter_error_response(request, msg):
    # TODO (Thurs Dec 11 16:54:45 2014): Send emergency email here.
    context = dict(error_message=msg)
    return http_response(request, conf.error_template, context)

def user_not_authenticated(request):
    return not request.user.is_authenticated()

def redirect_login_redirect(request, redirection_url):
    '''
    When a potential subject is trying to access an experiment page but is not
    yet logged in, we must first redirect them to the login page. 

    If they would like to proceed they will then either log in, or else if they
    do not already have an account, or forgotten their password, they will find
    their way to the signup sheet or to the forgot-my-password page, take care
    of business there and then log in.

    After all that, we redirect them to the page that they were trying to
    reach initially.
    '''

    push_redirection_url_stack(request, redirection_url)
    return redirect(login_url)

class LiveExperiment(object):
    '''
    A convenience class that provides direct access to many of the useful
    properties of the experiment that is currently live in the browser.  The
    relevant information is from three separate sources: The
    sessions.models.ExperimentSession model, the
    presenter.models.LiveExperimentSession model, and the request.session.
    '''

    def __init__(self, request):
        self.request_session = request.session
        self.live_session = models.LiveExperimentSession.objects.select_related().get(
                uid=self.request_session[conf.live_experiment]
            )
        self.experiment_session = self.live_session.experiment_session
        self.experiment_version = self.experiment_session.experiment_version
        self.experiment = self.experiment_version.experiment
        self.class_name = self.experiment.class_name
        self.name = self.experiment.name

    def get_nowplaying(self):
        '''
        A convienient link to live_session.get_nowplaying().
        '''
        return self.live_session.get_nowplaying()

#    # TODO (Sat 13 Sep 2014 21:39:52 BST): obsolete.
#    def set_nowplaying(self, slide_to_be_pickled):
#        '''
#        A convienient link to live_session.set_nowplaying().
#        '''
#        self.live_session.set_nowplaying(slide_to_be_pickled)
#
#    # TODO (Sat 13 Sep 2014 21:40:14 BST): obsolete.
#    def get_playlist(self):
#        '''
#        A convienient link to experiment_session.get_nowplaying().
#        '''
#        return self.experiment_session.get_playlist()
#
#    # TODO (Sat 13 Sep 2014 21:40:27 BST): obsolete.
#    def set_playlist(self, playlist_to_be_pickled):
#        '''
#        A convience function to set the playlist.
#        '''
#        self.experiment_session.set_playlist(playlist_to_be_pickled)

    def hangup(self, status='pause'):
        '''
        Shutdown a live experiment session, deleting the entry in the
        LiveExperimentSession db, hanging-up the ExperimentSession, deleting
        the live-experiment key in the request.session.
        '''

        self.live_session.pseudo_delete()
        del self.request_session[conf.live_experiment]
        self.experiment_session.hangup(status=status)

    # TODO (Sat 13 Sep 2014 22:44:45 BST): obsolete.
    def process_nowplaying_results(self):
        pass
#
#        '''
#        Process the results, if any, of the currently nowplaying slide. Push
#        them on to the playlist. 
#        '''
#        nowplaying = self.get_nowplaying()
#        try:
#            slide_results = nowplaying.process_results()
#        except:
#            slide_results = []
#
#        playlist = self.get_playlist()
#        playlist.push_results(nowplaying, slide_results)
#        self.set_playlist(playlist)
#
    def hangup_nowplaying(self):
        '''
        Turn off the nowplaying slide.
        '''
        #self.live_session.nowplayingfile = None
        #self.live_session.is_nowplaying = False
        #self.live_session.save()
        self.live_session.hangup_nowplaying()

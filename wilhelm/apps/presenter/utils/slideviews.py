'''
The slideviews utility module.
A module for selecting and returning a slideview object for the presenter
views.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist

#=============================================================================
# Wilhelm imports.
#=============================================================================
from .. import models, conf 
from apps import subjects, sessions
from apps.sessions import models as sessions_models
from apps.presenter.models import SlideToBeLaunchedInfo
from apps.subjects.utils import get_subject_from_request

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

def get_slide_to_be_launched_info(request):

    ''' If request has a key 'slide_to_be_launched_info_uid', get it and get
    the slide_to_be_launched_info object to which it corresponds. If no such
    object exists, return None '''
   
    try:
        slide_to_be_launched_info_uid\
            = request.session.get('slide_to_be_launched_info_uid')
    
        return SlideToBeLaunchedInfo.objects.select_related().get(uid=slide_to_be_launched_info_uid)

    except (KeyError, ObjectDoesNotExist):

        return None

class SlideViewFactory(object):

    def __init__(self, request, experiment_name, ping_uid_short):

        slide_to_be_launched_info = get_slide_to_be_launched_info(request)

        assert slide_to_be_launched_info is not None
        assert slide_to_be_launched_info.ping_uid_short == ping_uid_short
        assert slide_to_be_launched_info.name == experiment_name 

        self.slideview_type = slide_to_be_launched_info.slideview_type
        self.slideview_kwargs = slide_to_be_launched_info.slideview_kwargs
        self.ping_uid = slide_to_be_launched_info.ping_uid
        self.request = request
        self.experiment_name = experiment_name

    @classmethod
    def new(cls, request, experiment_name, ping_uid_short):

        slideview_factory = cls(request,
                                experiment_name,
                                ping_uid_short)

        SlideView = slideview_factory.getSlideView()

        slideview_args = slideview_factory.getSlideView_args()

        return SlideView(*slideview_args)

    def getSlideView(self):

        SlideView_map = {
            'LivePlaylistSlideView': LivePlaylistSlideView,
            'InitialPlaylistSlideView': InitialPlaylistSlideView,
            'PausedPlaylistSlideView': PausedPlaylistSlideView,
        }

        return SlideView_map[self.slideview_type]

    def getSlideView_args(self):

        SlideViewArgs_map = {
            'LivePlaylistSlideView': lambda : (self.slideview_kwargs['live_session_pk'], 
                                               self.ping_uid),
            'InitialPlaylistSlideView': lambda: (self.request, 
                                                 self.experiment_name, 
                                                 self.ping_uid),
            'PausedPlaylistSlideView': lambda : (self.request, 
                                                 self.slideview_kwargs['paused_experiment_session_pk'],
                                                 self.ping_uid)
        }

        return SlideViewArgs_map[self.slideview_type]()


##############################
####### Slide Views #######
##############################

### Parent SlideView class ###
class SlideView(object):

    def __init__(self, ping_uid):
        self.ping_uid = ping_uid

    def make_live(self, request, experiment_session):
        '''
        Make `experiment_session` (an ExperimentSession object instance in
        sessions.models.py) live.

        Create a LiveExperimentSession instance object. Link to that from the
        live_experiment in the session db.

        Return live_session instance.
        '''

        experiment_session.make_live()

        live_session = models.LiveExperimentSession.new(experiment_session,
                                                        request)

        request.session[conf.live_experiment] = live_session.uid

        return live_session
    
    def get_slide(self):

        '''
        Iterate the live experiment session's playlist and return the slide.
        '''

        logger.info('Get slide. Slide uid = %s.' % self.ping_uid)

        session_slide\
            =  self.live_session.iterate_playlist(ping_uid=self.ping_uid)

        assert session_slide.ping_uid == self.ping_uid,\
            "New session_slide ping_uid does not match view uid."

        session_slide.set_live_session(self.live_session)

        return session_slide

# TODO (Sat 30 Aug 2014 16:59:33 BST): What about RepeatPlaylistSlideView? Are
# they handled by this InitialPlaylistSlideView too?
class InitialPlaylistSlideView(SlideView):
    '''
    A class for serving the next slide, and taking care of business on the back
    end, when the experiment is new and must be started for the first time.
    '''
    def __init__(self, request, experiment_name, ping_uid):

        super(InitialPlaylistSlideView, self).__init__(ping_uid)

        subject = get_subject_from_request(request)
        #subject = subjects.models.Subject.objects.select_related().get(user = request.user)

        experiment_label = experiment_name.capitalize()

        # Start a new experiment session.
        experiment_session\
            = sessions.models.ExperimentSession.new(subject,
                                                    experiment_label)

        # And make it live.
        self.live_session = self.make_live(request, experiment_session)

class PausedPlaylistSlideView(SlideView):
    '''
    A class for serving the next slide, and taking care of business on the back
    end, when the experiment is paused in ExperimentSessions.
    That's it.
    '''
    def __init__(self, request, paused_experiment_session_pk, ping_uid):

        super(PausedPlaylistSlideView, self).__init__(ping_uid)

        paused_experiment_session = sessions_models.ExperimentSession.objects.get(
            pk = paused_experiment_session_pk
        )

        self.live_session = self.make_live(request, paused_experiment_session)

class LivePlaylistSlideView(SlideView):
    ''' A class for serving the next slide, and taking care of business in
    back-end in order to do this, in an experiment where the experiment is live
    in the browser session.  '''

    def __init__(self, live_session_pk, ping_uid):

        super(LivePlaylistSlideView, self).__init__(ping_uid)

        self.live_session = models.LiveExperimentSession.objects.select_related().get(
            pk = live_session_pk,
            )

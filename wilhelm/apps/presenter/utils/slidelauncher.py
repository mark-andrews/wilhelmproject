'''
The SlideLauncher module.
A SlideLauncher determines what slide is to be shown next, puts information
about that slide inside a database, and then returns a message to the subject.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging
import os

#=============================================================================
# Django imports.
#=============================================================================
from django.conf import settings
from django.template import Context, loader

#=============================================================================
# Wilhelm imports. 
#=============================================================================
from apps import archives, sessions
from . import viewutils
from apps.presenter.models import LiveExperimentSession, SlideToBeLaunchedInfo
from apps.presenter import conf
from apps.archives import models as archives_models
from apps.core.utils import strings, django
from apps.core.utils.docutils import rst2innerhtml
from apps.subjects.utils import (get_subject_from_request,
                                 has_unlimited_experiment_attempts)

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

######################################
####### Slide launcher factory #######
######################################

class SlideLauncherFactory(object):

    @classmethod
    def new(cls, request, experiment_name):

        'Return a new slide launcher.'

        launcher_factory = cls(request, experiment_name)

        if launcher_factory.is_some_session_live():
            launcher = launcher_factory.session_live_launcher()
        else:
            launcher = launcher_factory.session_not_live_launcher()

        return launcher

    def __init__(self, request, experiment_name):

        self.request = request
        self.browser_session = request.session
        self.experiment_name = experiment_name
        self.experiment = archives.models.Experiment.objects.get(
            class_name = experiment_name.capitalize()
        )

        assert not self.is_anonymous(), 'The user should not be anonymous'
        
        self.subject = get_subject_from_request(request)
        self.unlimited_attempts\
            = has_unlimited_experiment_attempts(self.subject)

        self.live_session_state_check()

    def is_anonymous(self):
        ''' Is the user anonymous?'''
        return not self.request.user.is_authenticated()

    #######################################################################
    ###### Database integrity checks ######################################
    #######################################################################
    def live_session_state_check(self):
        '''
        Check if the LiveExperimentSession is in a correct state.

        - At most one live session per subject.
        - That live session should point to a experiment session that is live.
        - If we have a browser session key pointing to a live sesion, it should
        be to one and only one.

        '''

        live_sessions\
            = LiveExperimentSession.objects.get_live_sessions(self.subject)

        assert len(live_sessions) <= 1, 'Live session not leq 1'

        # That session should be pointing to a live experiment session.
        if len(live_sessions) == 1:
            live_session = live_sessions[0]
            assert live_session.experiment_session.is_live, 'Session not live'

        # If there is a browser session key pointing to a live experiment,
        # there should be one and only one.
        if self.browser_session.has_key(conf.live_experiment):
            browser_live_sessions\
                = LiveExperimentSession.objects.filter(
                    pk=self.browser_session[conf.live_experiment]
                )

            n_browser_live_sessions = len(browser_live_sessions)
            assert n_browser_live_sessions == 1,\
                'There are %d browser live sessions' % n_browser_live_sessions

            # And that should be pointing to a status=live experiment.
            browser_live_session = browser_live_sessions[0]
            assert browser_live_session.experiment_session.is_live,\
                'Browser session unexpectedly pointing to live experiment session'

    def experiment_session_state_check(self):
        '''
        Test if the experiment session database is as it should be. This is
        important to catch errors in the state before they propagate.

        - The subject should have at most one live experiment session. (If
          there is one, it need not be in this browser session.)
        - If an experiment allows more than one attempt, all but the last
          attempt should be 'completed'. 
        
        '''
        # FIXME. Shouldn't this go in the sessions.models manager?
        _live_sessions_ErrMsg = strings.fill('''There should be only one live
                                             session per subject.  There are %d
                                             listed for subject %s. ''')

        experiment_sessions = self.get_all_my_experiment_sessions() 
        
        len_live_sessions = sum([exp_session.is_live 
                                 for exp_session in experiment_sessions])

        # Make the error msg.
        live_sessions_ErrMsg\
            = _live_sessions_ErrMsg % (len_live_sessions, self.subject)

        # Number of live sessions less than 1 assertion.
        assert len_live_sessions <= 1, live_sessions_ErrMsg

        _experiment_status_ErrMsg = strings.fill('''If the subject has more
                                                 than one experiment sessions
                                                 for the present experiment,
                                                 all but the most recent
                                                 attempts should be
                                                 "completed". For experiment %s
                                                 for subject %s, the statuses
                                                 are %s.''')

        statuses = [session.status for session in
                    self.get_my_this_experiment_sessions()]

        experiment_status_ErrMsg\
        = _experiment_status_ErrMsg % (self.experiment_name, self.subject,
                                       statuses)

        # All but last session is completed assertion.
        my_this_sessions = list(self.get_my_this_experiment_sessions())
        if len(my_this_sessions) > 1:
            assert all(
                [my_this_session.is_completed
                 for my_this_session in my_this_sessions[:-1]
                 ]
            ), experiment_status_ErrMsg

    #######################################################################
    #######################################################################
 
    def has_browser_any_live_experiment_session(self):
        '''
        Return True if there is live experiment session in the browser (key in
        browser session exists and does not point to None).
        '''

        # True only if browser session has no such key or key's value is None.
        session_is_none\
            = self.browser_session.get(conf.live_experiment, None) is None
        return not session_is_none

    def get_browser_live_experiment(self):
        '''
        Return the experiment that is currently live in the
        browser session. Return None if there is no experiment currently live.
        '''

        # FIXME. Will this raise an object not found exception is called when
        # the browser session does not have the conf.live_experiment key?
        return LiveExperimentSession.objects.get(
            pk=self.browser_session[conf.live_experiment]
            )

    def is_the_experiment_browser_live(self):
        '''
        Return True is the live experiment session in the browser is for
        self.experiment.
        '''

        live_session = self.get_browser_live_experiment()
        return live_session.experiment_session\
            .experiment_version.experiment == self.experiment

    def get_latest_experiment_session(self):
        '''
        Return the current/most-recent experiment session attempt.
        If no attempts have yet begun, None will be returned.
        '''
        return sessions.models.ExperimentSession.objects\
        .get_latest_experiment_session(self.experiment, self.subject)

    def get_all_my_experiment_sessions(self):
        '''Get all experiment sessions owned by subject.'''
        return sessions.models.ExperimentSession.objects\
            .get_all_my_experiment_sessions(self.subject)

    def get_my_this_experiment_sessions(self):
        '''
        Get all experiment sessions for experiment `experiment_name` owned by
        `subject`.
        '''
        return sessions.models.ExperimentSession.objects\
            .get_my_this_experiment_sessions(self.experiment, self.subject)

    #######################################################################
    #######################################################################
    # TODO (Wed 14 Jan 2015 19:26:18 GMT): Obsolete.
#    def _new_launcher(self):
#
#        if self.is_some_session_live():
#            # The subject has some session live.
#            launcher = self.session_live_launcher()
#        else:
#            # No session is live.
#            launcher = self.session_not_live_launcher()
#
#        return launcher

    #######################################################################
    #######################################################################

    def is_some_session_live(self):
        '''
        If `subject` has any experiment live somewhere, then return True, else
        return False.
        '''
        return LiveExperimentSession.objects.is_some_session_live(self.subject)

    def session_live_launcher(self):
        '''
        The launcher to be used when the subject does have a live session.
        If the session is not live in the browser, that means it is live in
        another browser session owned by `subject` and so we raise an error.
        '''
        if self.has_browser_any_live_experiment_session():
            launcher = self.browser_live_launcher()
        else:
            launcher = BlockedPlaylistSlideLauncher(self.experiment_name,
                                    conf.live_session_elsewhere_error)

        return launcher

    def browser_live_launcher(self):
        '''
        If the browser does have a live experiment, but it is not the
        `experiment_name` experiment, then raise an error.
        '''
        if self.is_the_experiment_browser_live():
            launcher = self.experiment_browser_live_launcher()
        else:
            # There is a browser session, but not for this experiment.
            launcher = BlockedPlaylistSlideLauncher(self.experiment_name,
                                    conf.another_experiment_error)

        return launcher

    def experiment_browser_live_launcher(self):
        '''
        The right experiment is live in the browser session. Check if it is not
        nowplaying. If it is, that's bad.
        '''

        live_session = self.get_browser_live_experiment()

        if not live_session.is_nowplaying:
            launcher = LivePlaylistSlideLauncher(live_session)
        else:
            launcher\
                = NowplayingBlockedPlaylistSlideLauncher(self.experiment_name,
                                                         live_session)

        return launcher

    #######################################################################
    #######################################################################

    def session_not_live_launcher(self):
        '''
        Check if subject has a session for this experiment completed 
        '''

        self.experiment_session_state_check()

        latest_experiment_session = self.get_latest_experiment_session() 

        if latest_experiment_session:
            launcher\
                = self.session_paused_or_completed(latest_experiment_session)
        else:
            launcher = InitialPlaylistSlideLauncher(self.experiment_name)

        return launcher
    
    def session_paused_or_completed(self, latest_experiment_session):

        if latest_experiment_session.is_paused:
            last_activity = latest_experiment_session.last_activity
            slides_done, slides_remaining\
                = latest_experiment_session.slides_completed_slides_remaining
            launcher = PausedPlaylistSlideLauncher(self.experiment_name,
                                           latest_experiment_session,
                                           slides_done,
                                           slides_remaining,
                                           last_activity)

        elif latest_experiment_session.is_completed:

            completions = latest_experiment_session.get_my_completions()

            if (self.unlimited_attempts
                    or (completions < self.experiment.attempts)):

                launcher = RepeatPlaylistSlideLauncher(self.experiment_name)

            else:
                launcher\
                    = BlockedPlaylistSlideLauncher(self.experiment_name,
                                                   conf.attempts_completed_error)
        return launcher

        # TODO (Sat 30 Aug 2014 12:08:03 BST): Should have an else:
        # here for if neither paused or completed. 

######################################
####### Slide Launchers ##############
######################################

class SlideLauncher(object):
    
    app_label = 'presenter'
    template_filename = 'launcher.html'

    def __init__(self, experiment_name, request=None):
        self.experiment_name = experiment_name
        self.template_data = {}
        self.slideview_kwargs = {}

        # TODO. Sept 16, 2014. We need this "skin" configuration information to
        # be somewhere else. E.g. in settings.py.
        self.cssfiles = ['front/css/main.css', 'bartlett/css/bartlett.css']
        self.jsfiles = ['base/widgets/hangup.js']
        self.template_data['cssfiles'] = self.cssfiles
        self.template_data['jsfiles'] = self.jsfiles
        self.template_data['experiment_name'] = experiment_name
        self.template_data['experiment_title'] = experiment_name.capitalize()
        self.template_data['PLAY_EXPERIMENT_ROOT'] = conf.PLAY_EXPERIMENT_ROOT

        self.ping_uid = django.uid() # This is the baptism.

        self.template_data['short_uid'] = self.ping_uid_short

        self.experiment = archives_models.Experiment.objects.get(
            class_name = self.experiment_name.capitalize()
        )

    @property
    def ping_uid_short(self):
        return self.ping_uid[:settings.UID_SHORT_LENGTH]

    def get_slide_to_be_launched_info_uid(self):
        '''
        This is the function that returns the tuple of info that is assigned as
        the value of the slide_to_be_launched key in the browser session.
        '''

        logger.info(self.experiment.name)

        slide_to_be_launched_info\
            = SlideToBeLaunchedInfo.new(experiment = self.experiment, 
                                        ping_uid = self.ping_uid,
                                        slideview_type=self.slideview_type,
                                        **self.slideview_kwargs)

        return slide_to_be_launched_info.uid

    def render(self):
        ''' Render the launcher's html template. '''

        template = loader.get_template(
            os.path.join(self.app_label, self.template_filename)
        )
        #context = Context(self.template_data)
        
        #return template.render(context)
        return template.render(self.template_data)


class LivePlaylistSlideLauncher(SlideLauncher):

    slideview_type = conf.slideview.LivePlaylistSlideView
    template_filename = 'live_experiment_launcher.html'

    def __init__(self, live_session): 

        super(LivePlaylistSlideLauncher, self).__init__(
            live_session.name
        )

        slides_done, slides_remaining\
            = live_session.experiment_session.slides_completed_slides_remaining

        self.slideview_kwargs['live_session_pk'] = live_session.pk

        self.template_data.update(
            (
                ('slides_done', slides_done),
                ('slides_remaining', slides_remaining),
                ('button', conf.button)
            )
        )

class PausedPlaylistSlideLauncher(SlideLauncher):

    slideview_type = conf.slideview.PausedPlaylistSlideView
    template_filename = 'resume_pause_launcher.html'

    def __init__(self, 
                 experiment_name, 
                 paused_experiment_session,
                 slides_done, 
                 slides_remaining, 
                 last_activity):

        super(PausedPlaylistSlideLauncher, self).__init__(experiment_name)

        self.slideview_kwargs['paused_experiment_session_pk']\
            = paused_experiment_session.pk

        self.template_data.update(
            (
                ('slides_done', slides_done),
                ('slides_remaining', slides_remaining),
                ('last_activity', last_activity),
                ('experiment_start_status', 'resume')
             )
        )

class InitialPlaylistSlideLauncher(SlideLauncher):
    
    slideview_type = conf.slideview.InitialPlaylistSlideView
    template_filename = 'initial_launcher.html'

    def __init__(self, experiment_name):

        super(InitialPlaylistSlideLauncher, self).__init__(experiment_name)

        instructions = self.experiment.current_version.playlist.instructions
        if instructions:
            rendered_instructions\
                = [rst2innerhtml(instruction) for instruction in instructions]
            self.template_data['instructions'] = rendered_instructions

        self.template_data['experiment_start_status'] = 'initial'

RepeatPlaylistSlideLauncher = InitialPlaylistSlideLauncher

class BlockedPlaylistSlideLauncher(SlideLauncher):

    template_filename = 'blocked_playlist_launcher.html'
    slideview_type = 'BlockedPlaylistView'

    def __init__(self, experiment_name, blockage_type):

        super(BlockedPlaylistSlideLauncher, self).__init__(experiment_name)

        self.template_data['blockage_type'] = blockage_type

class NowplayingBlockedPlaylistSlideLauncher(BlockedPlaylistSlideLauncher):

    def __init__(self, experiment_name, live_session):

        super(NowplayingBlockedPlaylistSlideLauncher, self).__init__(experiment_name,
                                                                     conf.session_nowplaying_error)


        live_session.hangup_nowplaying()



'''
The models for the sessions app.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
from collections import OrderedDict
import logging

#=============================================================================
# Django imports.
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.conf import settings

#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import conf
from apps.archives.models import (Experiment,
                                  ExperimentVersion)
import apps.subjects.models as subjects_models
from apps.core.utils import django, datetime
from apps.dataexport.utils import safe_export_data

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')


class ExperimentSessionManager(models.Manager):

    def get_experiment_sessions(self, experiment_pk):

        """Get all "ExperimentSession"s belonging to Experiment=experiment_pk.

        Find all "ExperimentSession"s whose parent Experiment has pk
        `experiment_pk`, e.g. 'Brisbane'.

        Returns:
            A QuerySet of Experiment objects.

        """

        return self.filter(experiment_version__experiment = experiment_pk)


    def get_all_my_experiment_sessions(self, subject):
        '''
        Get experiment sessions of `experiment_name` that belong to `subject`.
        '''
        return self.filter(subject=subject)

    # TODO (Mon Dec 15 18:44:42 2014): This should really check by subject not by
    # user.
    def get_my_this_experiment_sessions(self, experiment, user):
        '''
        Get experiment sessions of `experiment_name` that belong to `user`.
        '''
  
        return self.filter(subject=user,
                experiment_version__experiment=experiment).order_by('attempt')

    def data_export(self, experiment_version):

        """
        Return all the data from experiment version with label
        `experiment_version_label`.

        """

        export_dict = OrderedDict()

        key = 'Sessions'
        f = lambda: [experiment_session.data_export()
                     for experiment_session 
                     in self.get_all_experiment_version_sessions(experiment_version)]

        export_dict, exception_raised, exception_msg\
            = safe_export_data(export_dict, key, f)

        if exception_raised:
            logger.warning(exception_msg)

        # TODO (Sun 09 Aug 2015 16:32:29 BST): Export a dict, not a value of a dict
        return export_dict['Sessions'] 

    def get_all_experiment_version_sessions(self, experiment_version):

        """ 
        Return all experment sessions whose experiment version is
        `experiment_version`.

        """

        return self.filter(experiment_version=experiment_version).order_by('date_started')


    def get_latest_experiment_session(self, experiment, subject):
        '''
        Return the current/most-recent experiment session attempt.
        If no attempts have yet begun, None will be returned.
        '''

        my_experiment_sessions\
            = self.get_my_this_experiment_sessions(experiment, subject)

        if len(my_experiment_sessions):
            return my_experiment_sessions.last()

    def get_my_completions(self, experiment, subject):

        ''' 
        Get number of times `user` has completed experiment
        `experiment`.
        '''

        return len(self.filter(subject=subject,
                           experiment_version__experiment=experiment,
                           status=conf.status_completed))

        # TODO (Sun 21 Feb 2016 00:44:22 GMT): This was an accident waiting to happen.
        # An assert error would be raised if all sessions were not completed when this
        # function was called. Why should they be completed?

#        my_sessions = self.get_my_this_experiment_sessions(experiment, subject)
#
#        if my_sessions:
#            assert all([session.status == conf.status_completed 
#                        for session in my_sessions])
#            completions = len(my_sessions)
#        else:
#            completions = 0
#
#        return completions


class ExperimentSession(models.Model):

    ''' 
    An ExperimentSession is the where a given Subject performs a given
    ExperimentVersion. We need to know who is the subject, which is the
    experiment, when did it begin, when was last activity, what is its current
    status (is it live now, or paused, or completed). Most importantly, we need
    the experiment object itself, which is an instance of the experiment's
    playlist class.
    '''

    uid = models.CharField(max_length=settings.UID_LENGTH, primary_key=True)
    subject = models.ForeignKey(subjects_models.Subject)
    experiment_version = models.ForeignKey(ExperimentVersion) 

    #========================================================================
    # The generic foreign key to the playlist session instance.
    #========================================================================
    playlist_session_ct\
        = models.ForeignKey(ContentType, 
                            related_name = '%(app_label)s_%(class)s_as_playlist_session',
                            null=True)

    playlist_session_uid = models.CharField(max_length=settings.UID_LENGTH,
                                            null=True)
    playlist_session_fk = GenericForeignKey('playlist_session_ct', 
                                                    'playlist_session_uid')
    #=========================================================================

    attempt = models.IntegerField(default=0)
    parts_completed = models.IntegerField(default=0)

    date_started = models.DateTimeField(null=True)
    last_activity = models.DateTimeField(null=True)
    date_completed = models.DateTimeField(null=True)

    # TODO (Mon Dec 15 19:04:28 2014): Because we are not using a form, using
    # "choices" in a CharField does not do anything. 
    status_completed = conf.status_completed
    status_part_completed = conf.status_part_completed
    status_initialized = conf.status_initialized
    status_paused = conf.status_paused
    status_live = conf.status_live

    status = models.CharField(max_length=255, 
        choices = ((status_completed, 'Completed'), 
                    (status_part_completed, 'Part completed'),
                    (status_initialized, 'Initiated'),
                    (status_paused, 'Paused'),
                    (status_live, 'Live'))
        )

    objects = ExperimentSessionManager()
    
    #=========================================================================
    # Class methods
    #=========================================================================
    @classmethod
    def new(cls, 
            subject, 
            experiment_label):

        '''Create a new experiment session.

        * experiment_label could be either simply a class_name, e.g. Yarks, or
        else a experiment version label, Yarks_210101013_abd3qwa.

        '''

        try:

            experiment_version\
                = ExperimentVersion.objects.get(label = experiment_label)

        except ObjectDoesNotExist:

            experiment = Experiment.objects.get(class_name = experiment_label)
            experiment_version = experiment.current_version
        
        playlist_session = experiment_version.playlist.new_session_model()
        
        completions = cls.objects.get_my_completions(experiment, subject)

        now = datetime.now()

        experiment_session\
            = cls(subject=subject, 
                  experiment_version = experiment_version,
                  attempt=completions,
                  status = cls.status_initialized,
                  playlist_session_ct = ContentType.objects.get_for_model(playlist_session),
                  playlist_session_uid = playlist_session.uid,
                  uid = django.uid(),
                  date_started = now,
                  last_activity = now
                  )

        experiment_session.save()
        experiment_session.playlist_session.set_started()

        return experiment_session

    #=========================================================================
    # Instance methods.
    #=========================================================================
    def make_live(self, now=None):

        ''' Make the instance of this model live. Set its status to status_live.
        Update its time stamp. '''

        self.status = self.status_live
        self.stamp_time(now)

    def stamp_time(self, now=None):

        if now is None:
            now = datetime.now()

        self.last_activity = now
        self.save()


    def hangup(self, status='pause'):
        ''' Pause or complete the experiment session. If there are no slides
        remaining, then hangup with a 'completed' message.
        '''

        logger.debug('Experiment session hangup. Status=%s.' % status)

        self.hangup_nowplaying_safely()

        if status == 'pause':
            slides_completed, slides_remaining\
                = self.slides_completed_slides_remaining
            if slides_remaining:
                self.status = self.status_paused
            else:
                self.set_completed()
        elif status == 'completed':
                self.set_completed()

        self.last_activity = datetime.now()
        self.save()

    def set_completed(self):
        """
        Complete the experiment session; complete the playlist session too.
        """

        self.status = self.status_completed
        self.date_completed = datetime.now()
        self.playlist_session.set_completed()
        self.save()

    def iterate_playlist(self):
        return self.playlist_session.iterate()

    def get_nowplaying(self):
        return self.playlist_session.current_slide

    def hangup_nowplaying(self):
        self.playlist_session.stop_nowplaying()

    def hangup_nowplaying_safely(self):
        logger.debug('Experiment session safe nowplaying hangup.')
        current_slide_started, current_slide_completed\
            = (self.playlist_session.current_slide_in_playlist.started,
               self.playlist_session.current_slide_in_playlist.completed)

        if current_slide_started and (not current_slide_completed):
            logger.debug('Safe nowplaying hangup.')
            self.playlist_session.stop_nowplaying()

        logger.debug('Experiment session safe nowplaying hangup completed.')
 
    def get_my_completions(self):

        '''
        How many times I have I completed this experiment?
        '''

        return ExperimentSession.objects\
            .get_my_completions(self.experiment_version.experiment,
                                self.subject)

    def data_export(self):

        session_export_dict = OrderedDict()

        for key, f in [
                ('Start date', lambda: self.date_started),
                ('Session ID', lambda: self.uid),
                ('Attempt', lambda: self.attempt),
                ('Last activity', lambda: self.last_activity),
                ('Status', lambda: self.status)
        ]:

            session_export_dict, exception_raised, exception_msg\
                = safe_export_data(session_export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)


        export_dict = OrderedDict()

        for key, f in [
            ('Experiment session', lambda: session_export_dict),
            ('Subject information', lambda: self.subject.profile_export()),
            ('Live sessions', lambda: self.live_session_data_export()),
            ('Playlist information', lambda: self.playlist_session.data_export())
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def feedback(self):

        summary = dict()

        summary['experiment_name'] = self.experiment_version.experiment.name
        summary['start_date'] = self.date_started
        summary['attempt'] = self.attempt
        summary['status'] = self.status

        summary.update(self.subject.profile_export())
        summary.update(self.playlist_session.feedback())

        return summary

    def live_session_data_export(self):

        from apps.presenter.models import LiveExperimentSession

        return LiveExperimentSession.objects.data_export(self)

    #=========================================================================
    # Properties.
    #=========================================================================
    @property
    def playlist_session(self):
        playlist_session = self.playlist_session_ct.model_class()
        return playlist_session.objects.get(uid = self.playlist_session_uid)

    @playlist_session.setter
    def playlist_session(self, playlist_session):
        self.playlist_session_ct = ContentType.objects.get_for_model(playlist_session),
        self.playlist_sesion_uid = playlist_session.uid,

    @property
    def slides_completed_slides_remaining(self):
        return (self.playlist_session.slides_completed,
                self.playlist_session.slides_remaining)

    @property
    def is_live(self):
        ''' Return True if session is live. '''
        return self.status == self.status_live 

    @property
    def is_completed(self):
        ''' Return True if session is completed. '''
        return self.status == self.status_completed

    @property
    def is_paused(self):
        ''' Return True is session is paused. '''
        return self.status == self.status_paused

    @property
    def name(self):
        '''
        Return the name of the experiment in this session.
        '''
        return self.experiment_version.name

    class Meta:
        unique_together = (('subject', 'experiment_version', 'attempt'),)

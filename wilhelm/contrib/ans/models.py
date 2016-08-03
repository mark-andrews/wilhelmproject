from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
from collections import OrderedDict
import json
import logging

#=============================================================================
# Third party
#=============================================================================
import numpy as np
from scipy import stats
from jsonfield import JSONField

#=============================================================================
# Django imports
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

#=============================================================================
# Wilhelm imports
#=============================================================================
from contrib.base.models import (Widget, 
                                 SessionWidget,
                                 Slide,
                                 SessionSlide,
                                 Playlist,
                                 SessionPlaylist,
                                 SessionSlideAndPlaylistJoinModel)

from apps.core.utils import numerical, datetime
from apps.sessions.models import ExperimentSession
from apps.archives.models import Experiment
from apps.subjects.models import Subject

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')


def percentileofscore(allscores, score):
    percentile = stats.percentileofscore(allscores, score)
    return int(percentile.round())

class RandomDotDisplay(models.Model):

    uid = models.CharField(max_length=7, primary_key=True)
    density = models.FloatField()
    convex_hull_proportion = models.FloatField()
    radius_range = JSONField()
    bounding_circle_area = models.FloatField()
    seed = models.PositiveIntegerField()
    bounding_circle_parameters = JSONField()
    number_of_circles = models.PositiveIntegerField(null=True)
    circles = JSONField(null=True)

    @classmethod
    def new(cls, stimulus):

        assert len(stimulus['circles']) == stimulus['number_of_circles'],\
            'Len of "circles" != number_of_circles'

        kwargs = {}
        for key in ('uid', 
                    'density', 
                    'convex_hull_proportion', 
                    'radius_range',
                    'bounding_circle_area', 
                    'seed',
                    'bounding_circle_parameters',
                    'number_of_circles'):

            kwargs[key] = stimulus[key]

        try:
            random_dot_display = cls.objects.get(**kwargs)
        except ObjectDoesNotExist as e:

            assert len(cls.objects.filter(uid=kwargs['uid'])) == 0

            random_dot_display = cls.objects.create(**kwargs)
            random_dot_display.circles = stimulus['circles']
            random_dot_display.save()
            
        return random_dot_display

    @property
    def stimulus(self):

        '''
        Return the stimulus 
        
        '''

        _stimulus = {}
        for key in ('uid', 
                    'density', 
                    'convex_hull_proportion', 
                    'radius_range',
                    'bounding_circle_area', 
                    'seed',
                    'bounding_circle_parameters',
                    'number_of_circles',
                    'circles'):

            _stimulus[key] = getattr(self, key)

        return _stimulus


class ANSWidget(Widget):

    widget_type_defaults = Widget.widget_type_defaults.copy()
    widget_type_defaults.update(cssfiles = ('front/css/main.css',
                                            'bartlett/css/bartlett.css',
                                            'ans/css/ans.css'))
    widget_type_defaults.update(jsfiles = ('base/widgets/WidgetPrototype.js',))


    stimuli_list = JSONField(null=True)
    number_of_trials = models.PositiveIntegerField(null=True)
    start_message = models.CharField(null=True, max_length=100, default = 'Start')

    isi = models.FloatField(null=True,default=0.2)
    fadeInDuration = models.FloatField(null=True,default=0.2)
    fadeOutDuration = models.FloatField(null=True,default=0.2)
    timeOutDuration = models.FloatField(null=True,default=3)

    color = models.CharField(default='black', max_length=25, null=True)
    scale_factor = models.FloatField(null=True, default=100.0)
    separation = models.FloatField(null=True, default=10.0)

    @property
    def stimuli_list_length(self):
        return len(self.stimuli_list)

    @classmethod
    def new(cls,
            stimuli,
            number_of_trials,
            start_message,
            isi,
            fadeInDuration,
            fadeOutDuration,
            timeOutDuration,
            color,
            scale_factor,
            separation):

        for stimulus_pair in stimuli:

            left_display, right_display = stimulus_pair

            # Raise exceptions if either one is missing
            RandomDotDisplay.objects.get(uid = left_display)
            RandomDotDisplay.objects.get(uid = right_display)

        assert len(stimuli) >= number_of_trials

        kwargs = dict(stimuli_list = stimuli,
                      number_of_trials = number_of_trials,
                      start_message = start_message,
                      isi = isi,
                      fadeInDuration = fadeInDuration,
                      fadeOutDuration = fadeOutDuration,
                      timeOutDuration = timeOutDuration,
                      color = color,
                      scale_factor = scale_factor,
                      separation = separation)

        kwargs['widgettype'] = cls.get_widget_type()

        try:
            ans_test = cls.objects.get(**kwargs)
        except ObjectDoesNotExist as e:

            ans_test = cls.objects.create(**kwargs)

        return ans_test


    def get_widget_data(self):

        '''
        Get the general widget data. Exclude data that is widget session
        specific.
        '''

        return dict(start_message = self.start_message,
                    color = self.color,
                    separation = self.separation,
                    scale_factor = self.scale_factor,
                    fadeInDuration = self.fadeInDuration,
                    fadeOutDuration = self.fadeOutDuration,
                    timeOutDuration = self.timeOutDuration,
                    isi = self.isi)

    def get_widget_template_data(self):

        return dict(number_of_trials = self.number_of_trials)


class SessionANSWidget(SessionWidget):

    session_stimuli_list = JSONField(null=True)
    session_stimuli_list_permutation = JSONField(null=True)
    response_data = JSONField(null=True)

    @classmethod
    def new(cls, widget):

        session_widget = cls._new(widget)

        stimuli_list = widget.stimuli_list

        N = widget.stimuli_list_length
        K = widget.number_of_trials

        session_stimuli_list_permutation = numerical.permutation(N)[:K]
        session_stimuli_list = [stimuli_list[k] 
                                for k in session_stimuli_list_permutation]

        session_widget.session_stimuli_list = session_stimuli_list
        session_widget.session_stimuli_list_permutation = session_stimuli_list_permutation
        session_widget.save()

        return session_widget

    def get_session_widget_data(self):

        _session_stimuli = []
        for left_uid, right_uid in self.session_stimuli_list:

            _session_stimuli.append(
                dict(left = RandomDotDisplay.objects.get(uid = left_uid).stimulus,
                     right = RandomDotDisplay.objects.get(uid = right_uid).stimulus)
            )

        return _session_stimuli

    def get(self):
        logger.debug('Getting ANS test data.')

        self.set_started()
        widget_data = self.widget.get_widget_data()
        widget_data['stimuli'] = self.get_session_widget_data()

        return widget_data

    def post(self, data):
        logger.debug('Posting ANS test data.')

        def get_accuracy(stimulus_left, stimulus_right, choice):

            try:
                assert choice in (stimulus_left, stimulus_right), 'The chosen uid is not in the set of candidate uids'

                left_size = RandomDotDisplay.objects.get(uid = stimulus_left).number_of_circles
                right_size = RandomDotDisplay.objects.get(uid = stimulus_right).number_of_circles

                if left_size > right_size:
                    correct_response = stimulus_left
                else:
                    correct_response = stimulus_right

                if choice == correct_response:
                    accuracy = True
                else:
                    accuracy = False

            except (AssertionError, ObjectDoesNotExist) as e:

                logger.warning(e)

                left_size = None
                right_size = None
                accuracy = None

            return left_size, right_size, accuracy

        try:
            responses = json.loads(data['responses'])

            logger.debug('Processing data: %s' % repr(responses))

            response_data = []

            for datum in responses:

                try:

                    if datum['responseTime'] is None:
                        logger.debug('No responseTime. Missed trial?')
                        response_datetime = None
                    else:
                        response_datetime\
                            = datetime.fromtimestamp(datum['responseTime'])

                    if datum['latency'] is None:
                        logger.debug('No reaction time latency. Missed trial?')
                        latency = None
                    else:
                        latency = datum['latency']

                    if datum['response'] is None:
                        logger.debug('No response choice. Missed trial?')
                        choice = None
                    else:
                        choice = datum['response']


                    left_display_size, right_display_size, accuracy\
                        = get_accuracy(datum['stimulus_left'],
                                       datum['stimulus_right'],
                                       choice)

                    _d = OrderedDict()

                    _d['order'] = datum['order']
                    _d['stimulus_left'] = datum['stimulus_left']
                    _d['stimulus_right'] = datum['stimulus_right']
                    _d['stimulus_left_number_of_circles'] = left_display_size
                    _d['stimulus_right_number_of_circles'] = right_display_size
                    _d['stimulus_onset_datetime'] = datetime.fromtimestamp(datum['onset'])
                    _d['choice'] = choice
                    _d['accuracy'] = accuracy
                    _d['latency'] = latency
                    _d['response_datetime'] = response_datetime

                    response_data.append(_d)

                except Exception as e:
                    logger.warning('Could not process datum. %s ' % e.message)

                    response_data.append(None)

            self.response_data = response_data
            self.save()

        except Exception as e:
            logger.warning('Could not process data. %s ' % e.message)

        self.set_completed()

        if response_data:
            return response_data 

    def feedback(self):

        mean = lambda x: sum(x)/float(len(x))

        if self.response_data:

            number_of_trials = len(self.response_data)

            all_accuracy = [datum['accuracy'] for datum in self.response_data
                            if datum['accuracy'] != None]

            number_of_hits = len(all_accuracy)

            return number_of_trials, number_of_hits, mean(all_accuracy)

        else:

            return None, None, None


class ANSSlide(Slide):

    ans_widget = models.ForeignKey('ANSWidget')

    @classmethod
    def new(cls,
            stimuli,
            number_of_trials,
            start_message,
            isi,
            fadeInDuration,
            fadeOutDuration,
            timeOutDuration,
            color,
            scale_factor,
            separation):

        ans_widget = ANSWidget.new(stimuli,
                                   number_of_trials,
                                   start_message,
                                   isi,
                                   fadeInDuration,
                                   fadeOutDuration,
                                   timeOutDuration,
                                   color,
                                   scale_factor,
                                   separation)

        return cls._new(ans_widget = ans_widget)

    @property
    def widgets(self):
        return (self.ans_widget,)


class SessionANSSlide(SessionSlide):
    pass


class ANSPlaylist(Playlist):

    instructions = JSONField(null=True)
    max_slides = models.IntegerField(default=3, null=True, blank=True)

    # A place for miscellaneous information, stored as a JSON object.
    misc = JSONField(null=True)

    @classmethod
    def new(cls, slides, max_slides=3, instructions=None):

        playlist = cls._new(slides)
        playlist.instructions = instructions
        playlist.max_slides = max_slides
        playlist.save()

        return playlist

    # #####################################################################
    # TODO (Sun 14 Aug 2016 02:44:44 BST): This is a snarf-and-barf from
    # bartlett. Not good. Refactor things.
    # #####################################################################
    def get_experiment_parent(self):

        """Return the Experiment object parent.

        Return the Experiment object that is the parent of this playlist.
        Return None if there is no such Experiment object.

        Returns:
            An Experiment model instance.

        """

        condition = lambda experiment: experiment.current_version.playlist.uid == self.uid
        parent_experiments = filter(condition, Experiment.objects.all())

        if parent_experiments == []:
            return None
        else:
            error_msg = "This playlist object should have exactly one, not %d, Experiments object as a parent."
            number_of_parents = len(parent_experiments)
            assert number_of_parents == 1, error_msg % number_of_parents

            return parent_experiments.pop()

    def get_experiment_session_parents(self):

        """Return "ExperimentSession" parents.

        Get all the "ExperimentSession"s that are children of the Experiment
        that is the Experiment parent of this playlist.

        In other words, we want to find all "ExperimentSession"s that have the
        Experiment parent of this Playlist as their Experiment parent.

        Note that this Playlist will have one Experiment object as its parent.
        That Experiment will have possibly multiple "ExperimentVersion"s, each
        of which will be mapped to one Playlist. Those "Playlist"s will either
        be siblings of, or else be identical to, this Playlist. We want to find
        the "ExperimentSession"s whose Playlist objects are in this set.


        """

        experiment_parent = self.get_experiment_parent()

        if experiment_parent is None:
            return None

        else:

            return ExperimentSession.objects.filter(
                experiment_version__experiment = experiment_parent
            )

    def get_real_experiment_session_parents(self):

        """Return non-fake "ExperimentSession" parents.

        Get all the "ExperimentSession"s that are children of the Experiment
        that is the Experiment parent of this playlist, but filter out
        "ExperimentSession"s whose "Subject"s are not real, i.e. who are either
        "temp" or "test" subjects.

        """

        real_subjects = Subject.objects.get_real_subjects()

        try:
            return self.get_experiment_session_parents().filter(
                subject__in = real_subjects
            )

        except AttributeError:

            return None

    # #####################################################################
    # #####################################################################
    # #####################################################################

    def get_aggregate_scores(self):

        experiment_sessions = self.get_experiment_session_parents()

        approx_number_of_experiment_sessions = len(experiment_sessions)

        all_accuracy = []
        for experiment_session in experiment_sessions:

            playlist_session = experiment_session.playlist_session

            all_slides_feedback\
                = [element.session_slide.feedback() 
                   for element in playlist_session.filter_SlideAndPlaylistJoinModel]

            for slide_feedback in all_slides_feedback:
                 number_of_trials, number_of_hits, accuracy\
                     = slide_feedback['ANSWidget'] 

                 all_accuracy.append(accuracy)

        return approx_number_of_experiment_sessions, all_accuracy


def process_feedback(slide_feedback):

    for each_slide_feedback in slide_feedback:
        number_of_trials, number_of_hits, accuracy = each_slide_feedback['ANSWidget']


class SessionANSPlaylist(SessionPlaylist):

    @classmethod
    def new(cls, playlist):
        return cls._new(playlist)

    @classmethod
    def _new(cls, playlist):

        session_playlist = cls.initialize()

        session_playlist.set_parent_model('playlist', playlist)

        session_slides = []
        for slide in playlist.slides:
            for _ in xrange(playlist.max_slides):
                session_slide = slide.new_session_model()
                session_slides.append(session_slide)

        for i, session_slide in enumerate(session_slides):

            SessionSlideAndPlaylistJoinModel.new(container=session_playlist,
                                                 element=session_slide,
                                                 rank=i)

        return session_playlist


    def feedback(self):

        try:

            feedback = super(SessionANSPlaylist, self).feedback()

            try:
                approx_number_of_sessions, all_accuracy\
                    = self.playlist.get_aggregate_scores()
            except Exception as e:
                logger.warning('Trouble getting aggregation scores: %s.' % e)
                approx_number_of_sessions, all_accuracy = None, None

            if len(feedback['Slides']) > 0:

                overall_accuracy = []
                for slide_feedback in feedback['Slides']:
                    try:

                        number_of_trials, number_of_hits, accuracy\
                            = slide_feedback['ANSWidget']

                        if accuracy == None:
                            percentile = None
                        else:
                            overall_accuracy.append(accuracy)
                            percentile = percentileofscore(all_accuracy,
                                                           accuracy)

                    except Exception as e:

                        logger.warning('Could not calculate percentile: %s.' % e)
                        accuracy = None
                        percentile = None

                    slide_feedback['accuracy'] = accuracy
                    slide_feedback['percentile_of_score'] = percentile

            try:
                feedback['overall_accuracy'] = np.mean(overall_accuracy)
                feedback['overall_accuracy_percentile']\
                    = percentileofscore(all_accuracy, np.mean(overall_accuracy))

            except Exception as e:
                logger.warning('Could not calculate overall accuracy: %s.' % e)
                feedback['overall_accuracy'] = None
                feedback['overall_accuracy_percentile'] = None


            feedback['approx_number_of_sessions'] = approx_number_of_sessions

        except Exception as e:

            logger.warning('Something very unexpected happened: %s.' % e)
            feedback = {}

        return feedback

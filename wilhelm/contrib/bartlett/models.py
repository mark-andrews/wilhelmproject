from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import logging
from collections import defaultdict

#=============================================================================
# Third party imports.
#=============================================================================
from numpy.random import permutation
from scipy.stats import percentileofscore
from jsonfield import JSONField

#=============================================================================
# Django imports
#=============================================================================
from django.db.models import IntegerField

#=============================================================================
# Wilhelm imports
#=============================================================================
from contrib.base import models
from apps.core.utils import numerical
from apps.sessions.models import ExperimentSession
from apps.archives.models import Experiment
from apps.subjects.models import Subject
from .conf import recall_f1_score_number_of_relevant_items as f1_recall_denominator

#=============================================================================
# Widget models
#=============================================================================
from .widgets import (TextDisplay,
                      SessionTextDisplay,
                      WordlistDisplay,
                      SessionWordlistDisplay,
                      WordRecognitionTest,
                      SessionWordRecognitionTest,
                      WordRecallTest,
                      SessionWordRecallTest,
                      BinaryChoiceModel,
                      Tetris,
                      SessionTetris)

#=============================================================================
# Slides models
#=============================================================================
from .slides import (TextRecallMemoryTest,
                     SessionTextRecallMemoryTest,
                     TextRecognitionMemoryTest,
                     SessionTextRecognitionMemoryTest,
                     WordlistRecallMemoryTest,
                     SessionWordlistRecallMemoryTest,
                     WordlistRecognitionMemoryTest,
                     SessionWordlistRecognitionMemoryTest)

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

def process_feedback(slide_feedback):

    if slide_feedback['Test_type'] == 'Recognition':
        return 'Recognition', slide_feedback['accuracy']

    elif slide_feedback['Test_type'] == 'Recall':
        return 'Recall', slide_feedback['f1']

#=============================================================================
# Playlists models
#=============================================================================
class _Playlist(models.Playlist):

    class Meta:
        abstract = True

    instructions = JSONField(null=True)
    max_slides = IntegerField(default=3, null=True, blank=True)

    # A place for miscellaneous information, stored as a JSON object.
    misc = JSONField(null=True)

    @classmethod
    def new(cls, slides, max_slides=3, instructions=None):

        playlist = cls._new(slides)
        playlist.instructions = instructions
        playlist.max_slides = max_slides
        playlist.save()

        return playlist

    ####################
    # Instance methods #
    ####################
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

    def get_aggregate_scores(self):

        """Return aggregation of scores from the Experiment.

        NOTE that this function will be beastly slow. It should only be used in
        an asynchronous task queue.

        Go through all "ExperimentSession"s of the Experiment of which this
        Playlist is an descendant. Get all the Recognition and Recall results.
        Calculate the F1 score for the Recall tests, and the accuracy for the
        Recognition tests. Concatenate these scores into separate lists for
        Recall and Recognition.

        Returns:
            A tuple of (int, dict).
            The int is the number of subjects who did this experiment.
            The dictionary has two keys, Recall and Recognition, whose values
            are F1 and accuracy scores, respectively.

        """
       
        sessions = self.get_real_experiment_session_parents()

        try:

            real_subjects = Subject.objects.get_real_subjects()
            subjects = [session.subject.uid for session in sessions
                        if session.subject in real_subjects]

            n_unique_subjects = len(set(subjects))

        except:
            n_unique_subjects = None
            logger.warning('Could not calculate number of unique subjects.')

        aggregate_scores = None
        if sessions:

            try:
               
                results = []
                for session in sessions:

                    slides_completed, slides_remaining\
                        = session.slides_completed_slides_remaining

                    for slide_feedback in session.feedback()['Slides'][:slides_completed]:

                        results.append(process_feedback(slide_feedback))

                aggregate_scores = defaultdict(list)
                for test, score in results:
                    aggregate_scores[test].append(score)

                for memory_test, scores in aggregate_scores.items():

                    aggregate_scores[memory_test]\
                        = filter(lambda score: type(score) in (float, int),
                                 scores)

            except Exception as e:
                print(e)

                logger.warning('Something went wrong: %s.' % e)
    
                aggregate_scores = None

        return n_unique_subjects, aggregate_scores

    def save_aggregate_scores(self):

        """Save aggregate scores.

        If there are aggregate scores, save them as the value of the misc
        attribute.

        """

        n_unique_subjects, aggregate_scores = self.get_aggregate_scores()
        self.misc = (n_unique_subjects, aggregate_scores)
        self.save()


class _SessionPlaylist(models.SessionPlaylist):

    class Meta:
        abstract = True

    @classmethod
    def new(cls, playlist):
        return cls._new(playlist)

    @classmethod
    def _new(cls, playlist):

        session_playlist = cls.initialize()

        session_playlist.set_parent_model('playlist', playlist)
       
        session_slides\
            = session_playlist.make_session_slides(playlist.slides,
                                                   K=playlist.max_slides)

        for i, session_slide in enumerate(session_slides):

            models.SessionSlideAndPlaylistJoinModel.new(container=session_playlist,
                                                        element=session_slide,
                                                        rank=i)

        return session_playlist

    def make_session_slides(self, slides, K=1):

        """
        Randomly sample K slides. Make session slides from them.

        If anything goes wrong, return session slides for *all* slides.

        And we do not want the same text coming up as a word recall and a word
        recognition and we do not want the same wordlist doing the same.

        """


        try:

            N = len(slides)

            session_slides = []

            text_display_ids = []
            wordlist_display_ids = []

            for i in permutation(N):
                slide = slides[i]

                if slide.slide_type.name in ('TextRecognitionMemoryTest',
                                             'TextRecallMemoryTest'):

                    if slide.text_display_id not in text_display_ids:
                        session_slides.append(slide.new_session_model())


                if slide.slide_type.name in ('WordlistRecognitionMemoryTest',
                                             'WordlistRecallMemoryTest'):

                    if slide.wordlist_display_id not in wordlist_display_ids:
                        session_slides.append(slide.new_session_model())

                if len(session_slides) == K:
                    break

            return session_slides

        except Exception as e:
            # In case of error, return everything.
            logger.error('Could not permute and subsample slides: %s.' %
                         e.message)
            return [slides.new_session_model() for slide in slides]


    def feedback(self):

        try:

            feedback = super(_SessionPlaylist, self).feedback()

            try:
                n_unique_subjects, aggregate_scores = self.playlist.misc
            except Exception as e:
                logger.warning('Trouble getting aggregation scores: %s.' % e)
                n_unique_subjects, aggregate_scores = None, None

            if len(feedback['Slides']) > 0:

                for slide_feedback in feedback['Slides']:
                    try:
                        test_type, score = process_feedback(slide_feedback)
                        if score == None:
                            percentile = None
                        else:
                            percentile\
                                = percentileofscore(aggregate_scores[test_type],
                                                    score)
                            percentile = int(percentile.round())
                    except Exception as e:
                        logger.warning('Could not calculate percentile: %s.' % e)
                        percentile = None

                    slide_feedback['percentile_of_score'] = percentile

            feedback['n_unique_subjects'] = n_unique_subjects

        except Exception as e:

            logger.warning('Something very unexpected happened: %s.' % e)
            feedback = {}

        return feedback


class Playlist(_Playlist):
    pass

class PlaylistV2(_Playlist):
    pass

class SessionPlaylist(_SessionPlaylist):
    pass

class SessionPlaylistV2(_SessionPlaylist):

    '''
    A Playlist type to handle test/control wordlists.
    '''


    def make_session_slides(self, slides, K=1):

        """
        Randomly sample K slides. Make session slides from them.

        If anything goes wrong, return session slides for *all* slides.

        And we do not want the same text coming up as a word recall and a word
        recognition and we do not want the same wordlist doing the same.

        """


        try:

            N = len(slides)

            session_slides = []

            category_labels = []
            for i in permutation(N):
                slide = slides[i]

                if slide.slide_type.name in ('WordlistRecognitionMemoryTest',
                                             'WordlistRecallMemoryTest'):

                    test_or_control, category_label, test_type\
                        = slide.name.split('__')

                    if category_label not in category_labels:
                        session_slides.append(slide.new_session_model())
                        category_labels.append(category_label)

                if len(session_slides) == K:
                    break

            return session_slides


        except Exception as e:
            # In case of error, return everything.
            logger.error('Could not permute and subsample slides: %s.' %
                         e.message)
            return [slides.new_session_model() for slide in slides]

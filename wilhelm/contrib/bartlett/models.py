from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import logging

#=============================================================================
# Third party imports.
#=============================================================================
from numpy.random import permutation
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

#=============================================================================
# Playlists models
#=============================================================================
class Playlist(models.Playlist):
    instructions = JSONField(null=True)
    max_slides = IntegerField(default=3, null=True, blank=True)

    @classmethod
    def new(cls, slides, max_slides=3, instructions=None):

        playlist = cls._new(slides)
        playlist.instructions = instructions
        playlist.max_slides = max_slides
        playlist.save()

        return playlist

class SessionPlaylist(models.SessionPlaylist):

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

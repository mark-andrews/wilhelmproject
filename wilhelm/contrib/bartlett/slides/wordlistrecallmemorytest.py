from __future__ import absolute_import

#=============================================================================
# Standard library
#=============================================================================
import logging


#=============================================================================
# Wilhelm imports
#=============================================================================
from contrib.bartlett.utils import calculate_recall_rates
from apps.core import fields
from .slides import Slide, SessionSlide
from ..widgets import WordlistDisplay, WordRecallTest, Tetris

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class WordlistRecallMemoryTest(Slide):

    wordlist_display = fields.ForeignKey(WordlistDisplay)
    word_recall = fields.ForeignKey(WordRecallTest)
    tetris = fields.ForeignKey(Tetris)

    @classmethod
    def new(cls,
            name,
            wordlist,
            start_wordlist_msg,
            wordlist_display_times,
            option_length,
            start_memorytest_msg,
            game_duration=120,
            game_speed=500
            ):

 
        wordlist_display\
            = WordlistDisplay.new(wordlist = wordlist,
                                  start_msg = start_wordlist_msg,
                                  **wordlist_display_times)

        tetris = Tetris.new(duration = game_duration,
                            speed = game_speed)

        word_recall\
            = WordRecallTest.new(start_msg = start_memorytest_msg,
                                 option_length = option_length)

        return cls._new(
            name = name,
            wordlist_display = wordlist_display,
            word_recall = word_recall,
            tetris = tetris
        )

    @property
    def widgets(self):
        return (self.wordlist_display, self.tetris, self.word_recall)

    def get_slide_template_data(self):
        return dict(memorandum_type = 'word list')

class SessionWordlistRecallMemoryTest(SessionSlide):

    def feedback(self):

        try:
            session_widgets_feedback\
                = super(SessionWordlistRecallMemoryTest, self).feedback()

            summary = {}

            summary.update(session_widgets_feedback['WordlistDisplay'])
            summary.update(session_widgets_feedback['Tetris'])
            summary.update(session_widgets_feedback['WordRecallTest'])

            summary.update(calculate_recall_rates(summary['Wordlist'], 
                                                  summary['recalled_words']))
                  
            return summary

        except Exception as e:
            exception_type = e.__class__.__name__
            exception_msg = e.message
            logger.warning('Could not provide feedback. %s: %s.'\
                           % (exception_type, exception_msg))
                
            return None

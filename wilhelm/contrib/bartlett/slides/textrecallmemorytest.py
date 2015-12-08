from __future__ import absolute_import

#=============================================================================
# Standard library
#=============================================================================
import logging

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core import fields
from contrib.bartlett.utils import calculate_recall_rates
from .slides import Slide, SessionSlide
from ..widgets import TextDisplay, WordRecallTest, Tetris

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

class TextRecallMemoryTest(Slide):

    text_display = fields.ForeignKey(TextDisplay)
    word_recall = fields.ForeignKey(WordRecallTest)
    tetris = fields.ForeignKey(Tetris)

    @classmethod
    def new(cls,
            name,
            text,
            title,
            start_text_msg,
            reading_times,
            option_length,
            start_memorytest_msg,
            game_duration=120,
            game_speed=500):

        text_display = TextDisplay.new(text=text, 
                                       title=title, 
                                       start_msg=start_text_msg, 
                                       **reading_times)

        word_recall\
            = WordRecallTest.new(start_msg = start_memorytest_msg,
                                 option_length = option_length)


        tetris = Tetris.new(duration = game_duration,
                            speed = game_speed)

        return cls._new(name = name,
                        text_display = text_display,
                        word_recall = word_recall,
                        tetris = tetris)

    @property
    def widgets(self):
        return (self.text_display, self.tetris, self.word_recall)

    def get_slide_template_data(self):
        return dict(memorandum_type = 'text')

class SessionTextRecallMemoryTest(SessionSlide):

    def feedback(self):

        try:
            session_widgets_feedback\
                = super(SessionTextRecallMemoryTest, self).feedback()

            summary = {}

            summary.update(session_widgets_feedback['TextDisplay'])
            summary.update(session_widgets_feedback['Tetris'])
            summary.update(session_widgets_feedback['WordRecallTest'])

            text_tokens = map(str.lower, summary['Text_tokens'])

            summary.update(calculate_recall_rates(text_tokens, 
                                                  summary['recalled_words']))

            return summary

        except Exception as e:
            exception_type = e.__class__.__name__
            exception_msg = e.message
            logger.warning('Could not provide feedback. %s: %s.'\
                           % (exception_type, exception_msg))
                
            return None

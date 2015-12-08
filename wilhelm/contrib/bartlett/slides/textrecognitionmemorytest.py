from __future__ import absolute_import

#=============================================================================
# Standard library
#=============================================================================
import logging


#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core import fields
from apps.core.utils import strings
from .slides import Slide, SessionSlide
from ..utils import WordRecognitionTestStimuliCheck
from ..widgets import TextDisplay, WordRecognitionTest, Tetris

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')


class TextRecognitionMemoryTest(Slide):

    text_display = fields.ForeignKey(TextDisplay)
    word_recognition_test = fields.ForeignKey(WordRecognitionTest)
    tetris = fields.ForeignKey(Tetris)

    @classmethod
    def new(cls,
            name,
            title,
            text,
            inwords,
            outwords,
            start_text_msg,
            start_memorytest_msg,
            test_times,
            reading_times,
            game_duration=120,
            game_speed=500):

        WordRecognitionTestStimuliCheck(strings.tokenize(text),
                                        inwords,
                                        outwords)

        text_display = TextDisplay.new(text=text, 
                                       title=title, 
                                       start_msg=start_text_msg, 
                                       **reading_times)

        tetris = Tetris.new(duration = game_duration,
                            speed = game_speed)


        word_recognition_test\
            = WordRecognitionTest.new(inwords = inwords, 
                                      outwords = outwords,
                                      start_msg = start_memorytest_msg, 
                                      **test_times)

        return cls._new(
            name = name,
            text_display = text_display,
            word_recognition_test = word_recognition_test,
            tetris = tetris)

    @property
    def widgets(self):
        return (self.text_display, self.tetris, self.word_recognition_test)

    def get_slide_template_data(self):
        return dict(memorandum_type = 'text')

class SessionTextRecognitionMemoryTest(SessionSlide):

    def feedback(self):

        try:
            session_widgets_feedback\
                = super(SessionTextRecognitionMemoryTest, self).feedback()

            summary = {}

            summary.update(session_widgets_feedback['TextDisplay'])
            summary.update(session_widgets_feedback['Tetris'])
            summary.update(session_widgets_feedback['WordRecognitionTest'])

            return summary

        except Exception as e:
            exception_type = e.__class__.__name__
            exception_msg = e.message
            logger.warning('Could not provide feedback. %s: %s.'\
                           % (exception_type, exception_msg))
                
            return None

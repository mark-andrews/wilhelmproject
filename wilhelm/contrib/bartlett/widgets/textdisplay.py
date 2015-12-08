from __future__ import absolute_import
#=============================================================================
# Standard library
#=============================================================================
import json
import logging
 
#=============================================================================
# Wilhelm imports
#=============================================================================
from .widgets import Widget, SessionWidget
from contrib.bartlett.utils import nonstopword_unique_tokens
from contrib.stimuli.textual.models import TextStimulus
from apps.core import fields
from apps.core.utils import datetime
from apps.core.utils.datetime import approximate_minutes_from_seconds
from apps.core.utils.strings import abbreviate_text, tokenize
from apps.dataexport.utils import safe_export_data

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

class TextDisplay(Widget):

    '''
    Each text display widget displays a text to read and memorized.
    
    - textstimulus: A link to a TextStimulus object.
    - A boolean indicating if the title should be displayed.
    - A minimum reading time (in seconds).
    - A maximum reading time (in seconds).

    '''

    textstimulus = fields.ForeignKey(TextStimulus)
    minimum_reading_time = fields.DurationField(default=60)
    maximum_reading_time = fields.DurationField(default=180)

    @classmethod
    def new(cls,
            text,
            title,
            start_msg,
            minimum_reading_time,
            maximum_reading_time):

        textstimulus = TextStimulus.new(text = text, title = title)

        return cls._new(textstimulus = textstimulus, 
                        start_msg = start_msg,
                        minimum_reading_time = minimum_reading_time,
                        maximum_reading_time = maximum_reading_time)

    @property
    def widget_data(self):

        return dict(text = self.textstimulus.text,
                    title = self.textstimulus.title,
                    start_msg = self.start_msg,
                    minimum_reading_time = self.minimum_reading_time,
                    maximum_reading_time = self.maximum_reading_time)

    @property
    def text(self):
        return self.textstimulus.text

    @property
    def text_uid(self):
        return self.textstimulus.pk

    @property
    def text_checksum(self):
        return self.textstimulus.text_checksum

    @property
    def approximate_text_length(self):
        n = 10
        return n * (len(self.text.split()) // n)

    @property
    def title(self):
        return self.textstimulus.title

    def get_widget_template_data(self):

        return dict(approx_text_length = str(self.approximate_text_length),
                    title = self.title,
                    max_duration\
                    = approximate_minutes_from_seconds(
                        self.maximum_reading_time),
                    min_duration\
                    = approximate_minutes_from_seconds(
                        self.minimum_reading_time)
                    )



class SessionTextDisplay(SessionWidget):
    
    '''
    Is there anything other start and end needed?

    '''

    text_display_start = fields.DateTimeField()
    text_display_stop = fields.DateTimeField()

    def post(self, data):

        reading_data = json.loads(data['responses'])[0]
        print(reading_data)

        self.text_display_start\
            = datetime.fromtimestamp(reading_data['onset'])

        self.text_display_stop\
            = datetime.fromtimestamp(reading_data['offset'])

        self.set_completed()

        self.save()

    @property
    def reading_time(self):

        """

        Reading time is not (text_display_stop - text_display_start),
        because text_display_start is actually when the countdown to timeout
        begins. So text_display_start is a misnomer. To get the reading time,
        we need to add on the minimum reading time to the difference
        (text_display_stop - text_display_start).

        """

        try:

            return self.widget.minimum_reading_time\
                   + (self.text_display_stop
                      - self.text_display_start).total_seconds()

        except TypeError: 
            return None


    def data_export(self):

        export_dict = super(SessionTextDisplay, self).data_export()

        for key, f in [
            ('Text ID', lambda: self.widget.text_uid),
            ('Title', lambda: self.widget.title),
            ('Text', lambda: self.widget.text),
            ('Text abbreviated', lambda: abbreviate_text(self.widget.text)),
            ('Text checksum', lambda: self.widget.text_checksum),
            ('Minimum reading time', lambda: self.widget.minimum_reading_time),
            ('Maximum reading_time', lambda: self.widget.maximum_reading_time),
            ('Text display start datetime', lambda: self.text_display_start),
            ('Text display stop datetime', lambda: self.text_display_stop),
            ('Reading time', lambda: self.reading_time)
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def feedback(self):

        """
        Return a dict stating that the memorandum was a text, not a word list;
        the first line or so of the text; the tokens (words) of the text; the
        unique words of the text sans the stopwords; the reading time of the
        text.
        """

        summary = {}

        summary['Memoranda_type'] = 'Text'
        summary['Text_title'] = self.widget.title
        summary['Text_abbreviated'] = abbreviate_text(self.widget.text)
        summary['Text_tokens'] = tokenize(self.widget.text)
        summary['Text_keywords']\
            = nonstopword_unique_tokens(tokenize(self.widget.text))
        summary['Reading_time'] = self.reading_time

        return summary

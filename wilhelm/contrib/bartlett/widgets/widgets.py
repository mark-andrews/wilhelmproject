from __future__ import absolute_import

#=============================================================================
# Django imports.
#=============================================================================
from django.db.models import Model

#=============================================================================
# Wilhelm imports
#=============================================================================
from contrib.base import models as basemodels
from apps.core import fields
from apps.core.utils import numerical

#================================ End Imports ================================

class Widget(basemodels.Widget):

    '''
    The bartlett subclass of the main widget class.
    '''
    class Meta:
        abstract = True
        app_label = 'bartlett'

    start_msg = fields.TextField()

    # TODO (Tue 16 Sep 2014 02:54:50 BST): It would be nice to have a function that
    # does this widget_type_defaults over-riding.
    widget_type_defaults = basemodels.Widget.widget_type_defaults.copy()
    widget_type_defaults.update(cssfiles = ('front/css/main.css',
                                            'bartlett/css/bartlett.css',))
    widget_type_defaults.update(jsfiles = ('base/widgets/WidgetPrototype.js',))

class WordlistMixin(object):

    @property
    def wordlist(self):
        return self.wordliststimulus.wordlist
    
    
class SessionWidget(basemodels.SessionWidget):

    '''
    The bartlett subclass of the main session widget class.
    '''

    class Meta:
        abstract = True
        app_label = 'bartlett'

    @classmethod
    def new(cls, widget):
        '''
        Initiate a new session widget, passing in an instance of a widget
        class.
        '''

        return cls._new(widget)

class _BinaryChoiceModel(basemodels.BinaryChoiceModel):

    class Meta:
        abstract = True
        app_label = 'bartlett'

    pass

class SessionWordlistMixin(Model):

    class Meta:
        abstract = True
        app_label = 'bartlett'

    wordlist_permutation = fields.jsonField()

    @classmethod
    def new(cls, widget):
        '''
        Initiate a new session widget, passing in an instance of a widget
        class.
        '''

        session_widget =  cls._new(widget)

        widget_data = session_widget.widget.get_widget_data()
        session_widget.wordlist_permutation\
            = numerical.permutation(len(widget_data['wordlist']))

        session_widget.save()

        return session_widget

    def get(self):

        '''
        Return a python dict of the objects belonging to this widget that are
        to be sent to the client. This will be the dict returned by
        self.widget.get_widget_data(), but with the wordlist shuffled.
        '''

        widget_data = self.widget.get_widget_data()

        wordlist = widget_data['wordlist']

        widget_data['wordlist']\
            = [wordlist[i] for i in self.wordlist_permutation]

        return widget_data



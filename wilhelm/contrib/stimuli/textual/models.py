'''
Stimulus types
'''

from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import hashlib

#=============================================================================
# Django imports. 
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import models
from django.db.models import Model
from django.conf import settings

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core.utils import django

#================================ End Imports ================================

class TextStimulus(Model):

    text = models.TextField(null=True)
    title = models.TextField(default='A Text', null=True)

    @classmethod
    def new(cls, text, title='A Text'):
        text_stimulus, _created = cls.objects.get_or_create(text = text, 
                                                            title = title)
        return text_stimulus

    @property
    def text_checksum(self):
        """
        Return the sha1 checksum of the text.
        """

        h = hashlib.new('sha1')
        try:
            h.update(self.text)
        except UnicodeEncodeError as e:
            h.update(self.text.encode('utf-8'))
        return h.hexdigest()

class _abc_WordlistStimulus(Model):

    """
    The abstract base class for WordlistStimulus models.

    A WordlistStimulus model is basically a pointer to a wordlist but with
    additional helper functions.

    """

    class Meta:
        abstract = True

    #########################################################################
    uid = models.CharField(max_length=settings.UID_LENGTH, primary_key=True)
    name = models.CharField(max_length = 50, null = True)
    description = models.TextField(null=True)
    #########################################################################

    #########################################################################
    def get_item(self, word):

        """
        Get the wordlist item corresponding to the `word` in this list.

        """

        items = self.wordlist_items.filter(lexicon__word=word)

        if len(items) == 1:
            return items[0]
        elif len(items) > 1:
            raise MultipleObjectsReturned
        else:
            raise ObjectDoesNotExist

    #########################################################################

class WordlistStimulus(_abc_WordlistStimulus):

    #########################################################################
    @classmethod
    def new(cls, wordlist):

        '''
        Get or create.
        '''

        try:
            wordlist_stimulus = cls.get_wordlist(wordlist)

        except ObjectDoesNotExist:

            wordlist_stimulus = cls.objects.create(uid = django.uid())

            WordlistItems.new(wordlist_stimulus, wordlist)

        return wordlist_stimulus

    @classmethod
    def get_wordlist(cls, wordlist):

        """
        Get the WordlistStimulus object that points to `wordlist`.


        """

        matching_wordlist_stimuli = []
        for wordlist_stimulus in cls.objects.all():
            if wordlist_stimulus.wordlist == wordlist:
                matching_wordlist_stimuli.append(wordlist_stimulus)

        if len(matching_wordlist_stimuli) == 1:
            return matching_wordlist_stimuli.pop()

        
        elif len(matching_wordlist_stimuli) > 1:

            raise MultipleObjectsReturned

        else:

            raise ObjectDoesNotExist

    #########################################################################

    #########################################################################
    @property
    def wordlist_items(self):

        return WordlistItems.objects\
            .filter(wordlist_stimulus=self).order_by('order')

    @property
    def wordlist(self):

        return [member.word for member in self.wordlist_items]
                
    @property
    def length(self):

        return len(self.wordlist)

    #########################################################################


class WordlistTestStimulus(_abc_WordlistStimulus):

    #########################################################################
    @classmethod
    def new(cls, wordlist, expected_responses):

        '''
        Get or create.
        '''

        wordlist_stimulus_object = cls.get_wordlist(wordlist, expected_responses)

        if not wordlist_stimulus_object:

            wordlist_stimulus_object = cls.objects.create(uid = django.uid())

            WordlistTestItems.new(wordlist_stimulus_object, 
                                  wordlist,
                                  expected_responses)

        return wordlist_stimulus_object

    @classmethod
    def get_wordlist(cls, wordlist, expected_responses):

        """
        Find, if it exists, the instance object that points to this wordlist
        and expected responses.

        """

        assert len(wordlist) == len(expected_responses)

        wordlist_with_expected_responses = zip(wordlist, expected_responses)

        for wordlist_stimulus_object in cls.objects.all():

            if wordlist_stimulus_object.wordlist_with_expected_responses\
                    == wordlist_with_expected_responses:

                return wordlist_stimulus_object

    #########################################################################

    #########################################################################
    @property
    def wordlist_items(self):

        return WordlistTestItems.objects\
            .filter(wordlist_stimulus=self).order_by('order')

    @property
    def wordlist(self):

        """
        Return the word
        """

        return [member.word for member in self.wordlist_items]

    @property
    def wordlist_with_expected_responses(self):

        """
        Return the words and their expected_responses.
        """

        return [(member.word, member.expected_response) 
                for member in self.wordlist_items]


    @property
    def length(self):

        return len(self.wordlist)
    #########################################################################

 
class Lexicon(Model):
    word = models.CharField(max_length=50, primary_key=True, default='word')

class _abc_WordListItems(Model):

    class Meta:
        abstract = True

    uid = models.CharField(max_length=settings.UID_LENGTH,
                           primary_key=True)
    lexicon = models.ForeignKey(Lexicon, null=True)
    order = models.PositiveIntegerField(null=True)

    @classmethod
    def _new(cls, wordlist_stimulus, wordlist):

        wordlist_items = []

        for i, word in enumerate(wordlist):

            lexicon_item, _word_created\
                = Lexicon.objects.get_or_create(word = word)

            try:

                wordlist_item\
                = cls.objects.get(wordlist_stimulus = wordlist_stimulus, 
                                  lexicon = lexicon_item, 
                                  order = i)

            except ObjectDoesNotExist:

                wordlist_item\
                    = cls.objects.create(uid = django.uid(), 
                                         wordlist_stimulus = wordlist_stimulus, 
                                         lexicon = lexicon_item, 
                                         order = i)

            wordlist_items.append(wordlist_item)

        return wordlist_items

    @property
    def word(self):
        return self.lexicon.word


class WordlistItems(_abc_WordListItems):

    wordlist_stimulus = models.ForeignKey(WordlistStimulus,
                                          null=True)

    @classmethod
    def new(cls, *args, **kwargs):
        return cls._new(*args, **kwargs)


class WordlistTestItems(_abc_WordListItems):

    expected_response = models.NullBooleanField()
    wordlist_stimulus = models.ForeignKey(WordlistTestStimulus, 
                                          null=True)

    @classmethod
    def new(cls, wordlist_stimulus, wordlist, expected_responses):

        assert len(wordlist) == len(expected_responses)
        assert all([type(expected_response) is bool 
                    for expected_response in expected_responses])

        wordlist_items = cls._new(wordlist_stimulus, wordlist)

        assert len(wordlist_items) == len(expected_responses)

        for wordlist_item, expected_response in zip(wordlist_items, 
                                                    expected_responses):

            wordlist_item.expected_response = expected_response
            wordlist_item.save()

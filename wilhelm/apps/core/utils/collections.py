'''
A collection of handy utilities that arise in general situations.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import collections
import string
import random
#================================ End Imports ================================

def uniquelist(X):
    ''' Remove duplicates from a list but don't disrupt natural order.'''

    # We use OrderedDict to do unique elements.
    d = collections.OrderedDict()

    for x in X:
        d[x] = 0

    return d.keys()

def makewordlist(wordlist, uniquelist=True, foldcase='lowercase'):

    _foldcase_options = (('lowercase', string.lower),
                        ('uppercase', string.upper),
                        ('capitalize', string.capitalize),
                        (None, lambda x: x)
                        )

    foldcase_options = dict(_foldcase_options)

    try:

        wordlist = map(foldcase_options[foldcase], 
                        wordlist)

    except KeyError:

        foldcase_value_error = 'Unknown key %s' % foldcase
        foldcase_value_error\
            += ''' The specified foldcase option must be one of
                                the following types: %s.  ''' \
        % ', '.join(
            [str(_foldcase_option[0]) 
                for _foldcase_option in _foldcase_options]
        )

        raise KeyError(foldcase_value_error)

    if uniquelist:
        wordlist = collections.uniquelist(wordlist)

    return wordlist


def dictsubset(dictionary, keys):
    ''' 
    Extract out the keys "keys" from dictionary "dictionary" and return as
    a new dictionary.
    The keys argument must be an iterable.
    '''

    return {key : dictionary[key] for key in keys} # Dict comprehension.

def rshuffle(x):
    '''Return a shuffled copy of the list x.
    Useful for when you don't want an inplace shuffle.
    '''
    y = x[:]
    random.shuffle(y)
    return y

class Bunch(object):

    '''
    Convert a dictionary into an object so that the dictionary's key
    are now class instance attributes. 
    Taken from http://stackoverflow.com/a/2597440/1009979
    '''

    def __init__(self, adict):
        self.__dict__.update(adict)

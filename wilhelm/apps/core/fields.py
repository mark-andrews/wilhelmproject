'''
Provide all of django's model fields, plus custom model fields.
'''

#=============================================================================
# Standard library imports.
#=============================================================================
import string
import json

#=============================================================================
# Django imports.
#=============================================================================
from django.db import models
from django.core import exceptions
from django.conf import settings

#=============================================================================
# Third party imports.
#=============================================================================
from jsonfield import JSONField

#============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core import conf
from apps.core.utils import strings, collections

#================================ End Imports ================================

def could_not_convert(x, conversion_type):
    '''
    A generic error message raised when trying to convert something `x` to
    `conversion_type`.
    '''

    msg = 'Could not convert %s (%s) to %s.' % (str(x),
                                                type(x),
                                                conversion_type)
    return strings.msg(msg)

#=============================================================================
# The standard django fields.
#=============================================================================
class PositiveSmallIntegerField(models.PositiveSmallIntegerField):

    '''
    A small positive integer. Blank and null True by default.
    '''

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(PositiveSmallIntegerField, self).__init__(*args, **kwargs)

class PositiveIntegerField(models.PositiveIntegerField):

    '''
    A small positive integer. Blank and null True by default.
    '''

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(PositiveIntegerField, self).__init__(*args, **kwargs)

class ForeignKey(models.ForeignKey):

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(ForeignKey, self).__init__(*args, **kwargs)

class ManyToManyField(models.ManyToManyField):
    pass

class BooleanField(models.NullBooleanField):
    pass

class CharField(models.CharField):

    description = 'A standard CharField.'

    def __init__(self, *args, **kwargs):
        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)
        kwargs.setdefault('max_length', conf.charfield_max_length)

        super(CharField, self).__init__(*args, **kwargs)

#=============================================================================
# Custom model field classes.
#=============================================================================
class TitleField(models.TextField):
    description = 'The title of a stimulus to be displayed.'

    def __init__(self, *args, **kwargs):
        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(TitleField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        '''
        This is the from_python_to_db function.
        '''
        
        if not value:
            return ''

        try:
            return strings.titlecase(value)
        except:
            raise exceptions.ValidationError(
                could_not_convert(value, 'titlecase string.')
            )

class DateTimeField(models.DateTimeField):

    description = 'Date time field'

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(DateTimeField, self).__init__(*args, **kwargs)


class nameField(models.CharField):

    description = 'A name.'

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('max_length', settings.NAME_LENGTH)
        kwargs.setdefault('blank', True)

        super(nameField, self).__init__(*args, **kwargs)


class TextField(models.TextField):

    description = 'A standard TextField.'

    def __init__(self, *args, **kwargs):
        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(TextField, self).__init__(*args, **kwargs)

class WordlistField(models.TextField):
    '''
    A list of words. This list can be constrained to be unique, and all words
    can be converted to uppercase, lowercase, or capitalized.
    '''

    description = 'A list of words.'

    _foldcase_options = (('lowercase', string.lower),
                          ('uppercase', string.upper),
                          ('capitalize', string.capitalize),
                          (None, lambda x: x)
                          )

    foldcase_options = dict(_foldcase_options)

    foldcase_value_error = ''' The specified foldcase option must be one of
                               the following types: %s.  ''' \
    % ', '.join(
        [_foldcase_option[0] for _foldcase_option in _foldcase_options 
         if not _foldcase_option[0] is None]
    )

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        Initialize the arguments specific to WordlistField to False by default.

        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        self.uniquelist = kwargs.pop('uniquelist', False)
        self.foldcase = kwargs.pop('foldcase', None)

        super(WordlistField, self).__init__(*args, **kwargs)
    
    def fold(self, wordlist):
        '''
        Words can be forced to be uppercase, lowercase, or capitalized.
        They can also be forced to be a unique list.
        '''

        folded_wordlist = map(self.foldcase_options[self.foldcase], wordlist)

        if self.uniquelist:
            return collections.uniquelist(folded_wordlist)
        else:
            return folded_wordlist


    def get_prep_value(self, wordlist):
        '''
        The wordlist is json'ised and stored as a str.
        '''
        
        if not wordlist:
            return ''

        try:
            return json.dumps(self.fold(wordlist))
        except ValueError:
            raise exceptions.ValidationError(
                could_not_convert(wordlist, 'json string')
            )

    def to_python(self, value):
        '''
        The stored value is a json str. Load it and return it.
        '''

        if not value:
            return []

        try:
            return json.loads(value)
        except ValueError:
            raise exceptions.ValidationError(
                could_not_convert(value, 'list')
           )

class DurationField(models.FloatField):

    '''
    A temporal duration in seconds.
    '''

    description = "Temporal duration in units of seconds."

    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(DurationField, self).__init__(*args, **kwargs)


# TODO (Wed 10 Sep 2014 16:10:33 BST): This is not to be trusted.
#class DurationField(models.FloatField):
#
#    '''
#    A temporal duration. Default unit is milliseconds.
#    '''
#
#    description = "Temporal duration in units of %(units)s"
#
#    # TODO (Sat 23 Aug 2014 03:04:09 BST): This thing here can cause *real*
#    # trouble.
#    #__metaclass__ = models.SubfieldBase
#
#    _duration_units = (
#                       ('milliseconds', 1.0),
#                       ('seconds', 1e3),
#                       ('minutes', 1e3 * 60.0),
#                       ('hours', 1e3 * 60.0 * 60.0),
#                       ('days', 1e3 * 60.0 * 60.0 * 24),
#                       ('weeks', 1e3 * 60.0 * 60.0 * 24 * 7),
#                       ('months', 1e3 * 60.0 * 60.0 * 24 * 365.242/12),
#                       ('years', 1e3 * 60.0 * 60.0 * 24 * 365.242)
#                       )
#
#    duration_units = dict(_duration_units)
#
#    duration_units_value_error = '''
#    The specified type of units must be one of the following type: %s.
#    ''' % ', '.join([_duration_unit[0] for _duration_unit in _duration_units])
#
#    def to_milliseconds(self, value):
#        return value * self.to_milliseconds_multiplier
#
#    def from_milliseconds(self, value):
#        return value / float(self.to_milliseconds_multiplier)
#
#
#    def __init__(self, *args, **kwargs):
#        '''
#        If units is not one of the types specified in duration_units, then
#        raise an error.
#        '''
#
#        units = kwargs.pop('units', 'milliseconds') 
#
#        try:
#            self.to_milliseconds_multiplier = self.duration_units[units]
#        except KeyError:
#            raise ValueError(strings.msg(self.duration_units_value_error))
#
#
#        kwargs.setdefault('null', True)
#        kwargs.setdefault('blank', True)
#
#        super(DurationField, self).__init__(*args, **kwargs)
#
#    def get_prep_value(self, value):
#        '''
#        This is the from_python_to_db function.
#        '''
#        
#        if not value:
#            return ''
#        
#        else:
#
#            try:
#                return self.to_milliseconds(value)
#            except ValueError:
#                raise exceptions.ValidationError(
#                    could_not_convert(value, 'int')
#                )
#
#
#    def to_python(self, value):
#        '''
#        This is the from_db_to_python function.
#        '''
#
#        if not value:
#            return None
#
#        else:
#
#            try:
#                return self.from_milliseconds(value)
#            except (ValueError, TypeError):
#                raise exceptions.ValidationError(
#                    could_not_convert(value, 'float')
#            )
#
class PermutationIntegerListField(models.TextField):

    not_an_integer_list = 'Is %s a permutation of integers 0 to N-1?'

    #__metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(PermutationIntegerListField, self).__init__(*args, **kwargs)

    def get_prep_value(self, integer_list):
        '''
        This is the from_python_to_db function.
        '''
        
        if not integer_list:
            return ''

        try:

            integer_list = list(integer_list)

            assert min(integer_list) == 0
            N = max(integer_list)
            assert type(N) is int
            assert sorted(integer_list) == range(N)

            return json.dumps(integer_list)
            
        except AssertionError:
             raise exceptions.ValidationError(
                strings.msg(self.not_an_integer_list % integer_list)
             )

        except TypeError:
            raise exceptions.ValidationError(
                could_not_convert(integer_list, 'json_str')
            )

    def to_python(self, value):
        ''' Convert the string (e.g. '4,5,6,...') to an integer list 
        [4, 5, 6, ... ]
        '''

        if not value:
            return []
        try:
            return json.loads(value)
        except:
            raise exceptions.ValidationError(
                could_not_convert(value, 'integer list')
            )

class uidField(models.CharField):

    #__metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        Initialize the arguments specific to WordlistField to False by default.

        '''

        kwargs.setdefault('primary_key', True)
        kwargs.setdefault('max_length', settings.UID_LENGTH)

        super(models.CharField, self).__init__(*args, **kwargs)

class jsonField(JSONField):

    def __init__(self, *args, **kwargs):

        '''
        Initialize null = blank = True by default.
        '''

        kwargs.setdefault('null', True)
        kwargs.setdefault('blank', True)

        super(jsonField, self).__init__(*args, **kwargs)


#class jsonField(models.TextField):
#
#    description = 'A list of responses.'
#
#    __metaclass__ = models.SubfieldBase
#
#    _convert_to = 'json str'
#    _convert_from = 'loaded json'
#
#    def __init__(self, *args, **kwargs):
#
#        '''
#        Initialize null = blank = True by default.
#        Initialize the arguments specific to WordlistField to False by default.
#
#        '''
#
#        kwargs.setdefault('null', True)
#        kwargs.setdefault('blank', True)
#
#        super(models.TextField, self).__init__(*args, **kwargs)
#
#    def get_prep_value(self, value):
#        '''
#        This is the from_python_to_db function.
#        '''
#
#        print('get_prep')
#        
#        try:
#
#            return json.dumps(value)
#
#        except ValueError:
#            raise exceptions.ValidationError(
#                could_not_convert(value, self._convert_to)
#            )
#
#
#    def to_python(self, value):
#
#        print('to_pyt')
#
#        try:
#            return json.loads(value)
#        except ValueError:
#            raise exceptions.ValidationError(
#                could_not_convert(value, self._convert_from)
#           )

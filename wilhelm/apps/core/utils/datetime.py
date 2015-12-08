from __future__ import absolute_import, division

#=============================================================================
# Standard library imports
#=============================================================================
import datetime
from datetime import date

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils import strings


#================================ End Imports ================================

strptime = datetime.datetime.strptime

def now():
    return datetime.datetime.now()

def fromtimestamp(timestamp, milliseconds=True):
    '''

    Given a string representing a seconds or milliseconds (default) since the
    epoch, convert to a python datetime.

    '''

    timestamp = float(timestamp)

    if milliseconds:
        divisor = 1000.0 
    else:
        divisor = 1.0

    return datetime.datetime.fromtimestamp(timestamp/divisor)

def convert_duration(duration, convert_from='seconds', convert_to='seconds'):

    '''
    Convert from one temporal duration to another. 
    Acceptable units are milliseconds, seconds, minutes, hours, days, weeks,
    months, and years. 
    '''

    _duration_units = (
                       ('milliseconds', 1e-3),
                       ('seconds', 1.0),
                       ('minutes', 60.0),
                       ('hours', 60.0 * 60.0),
                       ('days',  60.0 * 60.0 * 24),
                       ('weeks', 60.0 * 60.0 * 24 * 7),
                       ('months', 60.0 * 60.0 * 24 * 365.242/12),
                       ('years', 60.0 * 60.0 * 24 * 365.242)
                       )


    duration_units_value_error = '''
    The specified type of units must be one of the following type: %s.
    ''' % ', '.join([_duration_unit[0] for _duration_unit in _duration_units])

    duration_units = dict(_duration_units)

    try:
        to_seconds = duration * duration_units[convert_from]

        return to_seconds / duration_units[convert_to]

    except KeyError:

        print(strings.msg(duration_units_value_error))
        raise

def age_from_dob(dob):
    '''
    Given a birth date as a datetime.date instance, return a their age as an
    integer.

    Taken from http://stackoverflow.com/a/9754466/1009979

    '''
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def approximate_minutes_from_seconds(seconds):
    ''' Given a number of seconds, return as number of minutes, rounding
    appropriately. If number is less than 120, state result as seconds.'''

    seconds = float(seconds)

    if seconds < 120:
        duration_str = str(int(seconds)) + ' seconds'
    else:
        duration_str = str(int(seconds/60)) + ' minutes'

    return duration_str

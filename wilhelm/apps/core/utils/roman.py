'''
The following code converts integers to Roman numerals. I am using it for
version numbering.  It was taken and modified from the free software code
found on Oct 23, 2013 at
http://svn.python.org/projects/python/branches/pep-0384/Doc/tools/roman.py
'''

import re


#Define exceptions.
class InvalidRomanNumeralError(Exception): 
    pass
class OutOfRangeError(InvalidRomanNumeralError): 
    pass
class NotIntegerError(InvalidRomanNumeralError): 
    pass

#Define integer to numeral digit mapping.
romanNumeralMap = (('m',  1000),
                   ('cm', 900),
                   ('d',  500),
                   ('cd', 400),
                   ('c',  100),
                   ('xc', 90),
                   ('l',  50),
                   ('xl', 40),
                   ('x',  10),
                   ('ix', 9),
                   ('v',  5),
                   ('iv', 4),
                   ('i',  1))

def toRoman(n):
    """Convert integer to Roman numeral"""

    try:
        n = int(n)
    except: # I know general excepts like this are not recommended, but
            #    ValueErrors were not being caught.
        
        raise NotIntegerError(
        '''Only integers can be converted to Roman numerals.
        I tried to convert %s to an integer, but that did not work.
        ''' % str(n)
        )

    if not (0 < n < 5000):
        raise OutOfRangeError("The integer must be range 1..4999.")

    result = ""
    for numeral, integer in romanNumeralMap:
        while n >= integer:
            result += numeral
            n -= integer
    return result



#Define pattern to detect valid Roman numerals
romanNumeralPattern = re.compile("""
    ^                   # beginning of string
    M{0,4}              # thousands - 0 to 4 M's
    (CM|CD|D?C{0,3})    # hundreds - 900 (CM), 400 (CD), 0-300 (0 to 3 C's),
                        #            or 500-800 (D, followed by 0 to 3 C's)
    (XC|XL|L?X{0,3})    # tens - 90 (XC), 40 (XL), 0-30 (0 to 3 X's),
                        #        or 50-80 (L, followed by 0 to 3 X's)
    (IX|IV|V?I{0,3})    # ones - 9 (IX), 4 (IV), 0-3 (0 to 3 I's),
                        #        or 5-8 (V, followed by 0 to 3 I's)
    $                   # end of string
    """ ,re.VERBOSE|re.I)

def fromRoman(s):
    """convert Roman numeral to integer"""
    if not s:
        raise InvalidRomanNumeralError('Input can not be blank')
    if not romanNumeralPattern.search(s):
        raise InvalidRomanNumeralError('Invalid Roman numeral: %s' % s)

    result = 0
    index = 0
    for numeral, integer in romanNumeralMap:
        while s[index:index+len(numeral)] == numeral:
            result += integer
            index += len(numeral)
    return result

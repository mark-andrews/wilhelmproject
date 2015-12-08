'''
General purpose string utilities.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import string 
import re
from random import getrandbits, choice
import textwrap
from textwrap import TextWrapper

#================================ End Imports ================================

def deletechars(s, exclude_chars):
    ''' Fast deletion of characters from string.
    It uses a dummy translation table, and so no mapping is applied, and we
    just delete the exclude_chars characters.
    '''
    phony_translate_table = string.maketrans("","")
    return s.translate(phony_translate_table, exclude_chars)

def deletepunctuation(s):
    ''' Fast deletion of punctuation from string'''
    return deletechars(s,string.punctuation)

def fill(s):
    ''' 
    Remove extra whitespace and linebreaks from a string,
    and return as a single line. 
    '''
    return ' '.join(s.split())

def tokenize(text, foldcase=True):
    ''' 
    A very cheap and easy tokenization.
    First, remove "'s". For example, "dog's" becomes "dog".
    Second, zap utf-8 chars.
    Then, remove all punctuation and, by default, fold upper and lower case words
    and then split by whitespace.
    '''

    text = re.sub(r'\'s','', text)
    s = ''.join([s for s in text if s in string.printable])

    s = str(s) # Got to convert it to str.
    s = deletepunctuation(s)

    if foldcase:
        s = s.lower()
    return s.split()

def IsDigitString(S):
    '''
    Returns True if s is a string of digits. Else return False.
    '''
    return all([s in string.digits for s in S])

def linejoin(*args):
    '''
    Join all strings given as args by new lines.
    '''
    return '\n'.join(args)

def titlecase(S, exceptions=None):
    '''
    Convert a text, usually a sentence, into titlecase, i.e. all words
    capitalized except for some stop words.

    Based on
    http://stackoverflow.com/a/3729957/1009979
    '''

    if exceptions is None:
        exceptions = [] 

    exceptions += ['a', 'the', 'an', 'to', 'of', 'in', 'is']

    words = S.split()

    return ' '.join(
        [words[0].capitalize()]
        + [word in exceptions and word or word.capitalize() 
           for word in words[1:]]
    )

def sentencecase(S, exceptions=None):
    '''
    Convert a text, usually a sentence, into sentence, i.e. first word
    capitalized and all others lower except for some exception words.

    '''

    if exceptions is None:
        exceptions = [] 

    words = S.split()

    return ' '.join(
        [words[0].capitalize()]
        + [word in exceptions and word or word.lower() 
           for word in words[1:]]
    )

def camelToSnake(s):
    """ 
    Convert camelcase to snake case.
    Relevant StackOverflow question: 
    http://stackoverflow.com/a/1176023/293064
    author: 'Jay Taylor [@jtaylor]'

    """
 
    _underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
    _underscorer2 = re.compile('([a-z0-9])([A-Z])')
    subbed = _underscorer1.sub(r'\1_\2', s)
    return _underscorer2.sub(r'\1_\2', subbed).lower()

def wrapit(text, width=80, sep='\n'):

    filled_out_text = fill(text.strip())
    wrapped_text = textwrap.wrap(filled_out_text, width=width)

    return sep.join(wrapped_text)

def msg(text, sep=' ', *args, **kwargs):
    '''
    A convenience to neatly format message strings, such as error messages.
    '''

    text_wrapper = TextWrapper(*args, **kwargs)
    return sep.join(text_wrapper.wrap(text.strip()))

def uid(k=40):
    ''' Generate a k hex digit unique identifier.'''
    uidformat = '%%0%dx' % k
    return uidformat % getrandbits(k*4) # Each hex digit is 2^4 bits.

def dec2bin(n, K=None):
    '''
    Convert decimal integer n to a binary integer.
    If K is not None, leading zeros will be prepended so that the
    resulting binary integer will be bit length K. For example, the
    binary integer corresponding to 27 is 11011. If, however, we want this
    represented as an 8 bit number, i.e. 00011011, we would use
    dec2bin(27, K=8)
    '''
    try:
        return format(n, str(int(K)) + 'b')
    except:
        return format(n, 'b')

def bin2dec(b):
    '''Assuming that b is a binary integer string like '101101', return the
    decimal integer to which this corresponds.'''
    return int(b, 2)

def rpassword(k=8):
    '''
    Generate a random password of length k.
    '''

    symbol_sets = (string.digits,
                   string.uppercase,
                   string.lowercase)

    return ''.join([choice(choice(symbol_sets)) for _ in xrange(k)])

def wrap_text(text):

    if isinstance(text, basestring):

        text_wrapper = TextWrapper()

        if len(text) > text_wrapper.width:

            return text_wrapper.fill(text.strip())

    return text

def abbreviate_text(text, max_length=50):

    if isinstance(text, basestring):

        if len(text) > max_length:

            words = text.split()
            first_words = []
            for word in words:

                first_words.append(word)

                if len(' '.join(first_words)) > max_length:
                    break


            text = ' '.join(first_words)
            return text.strip().strip('.') + '...'

    return text

def rmstopwords(words, stopwords=None):
    
    if stopwords is None:

        stopwords = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
                     'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
                     'w', 'x', 'y', 'z', 'th', 're', 'nd', 'ed', 'wa', 'ha',
                     'about', 'above', 'across', 'after', 'afterwards',
                     'again', 'against', 'all', 'almost', 'alone', 'along',
                     'already', 'also', 'although', 'always', 'am', 'among',
                     'amongst', 'amoungst', 'amount', 'an', 'and', 'another',
                     'any', 'anyhow', 'anyone', 'anything', 'anyway',
                     'anywhere', 'are', 'around', 'as', 'at', 'back', 'be',
                     'became', 'because', 'become', 'becomes', 'becoming',
                     'been', 'before', 'beforehand', 'behind', 'being',
                     'below', 'beside', 'besides', 'between', 'beyond', 'bill',
                     'both', 'bottom', 'but', 'by', 'call', 'can', 'cannot',
                     'cant', 'co', 'computer', 'con', 'could', 'couldnt',
                     'cry', 'de', 'describe', 'detail', 'do', 'done', 'down',
                     'due', 'during', 'each', 'eg', 'eight', 'either',
                     'eleven', 'else', 'elsewhere', 'empty', 'enough', 'etc',
                     'even', 'ever', 'every', 'everyone', 'everything',
                     'everywhere', 'except', 'few', 'fifteen', 'fify', 'fill',
                     'find', 'fire', 'first', 'five', 'for', 'former',
                     'formerly', 'forty', 'found', 'four', 'from', 'front',
                     'full', 'further', 'get', 'give', 'go', 'had', 'has',
                     'hasnt', 'have', 'he', 'hence', 'her', 'here',
                     'hereafter', 'hereby', 'herein', 'hereupon', 'hers',
                     'herse"', 'him', 'himse"', 'his', 'how', 'however',
                     'hundred', 'i', 'ie', 'if', 'in', 'inc', 'indeed',
                     'interest', 'into', 'is', 'it', 'its', 'itse"', 'keep',
                     'last', 'latter', 'latterly', 'least', 'less', 'ltd',
                     'made', 'many', 'may', 'me', 'meanwhile', 'might', 'mill',
                     'mine', 'more', 'moreover', 'most', 'mostly', 'move',
                     'much', 'must', 'my', 'myse"', 'name', 'namely',
                     'neither', 'never', 'nevertheless', 'next', 'nine', 'no',
                     'nobody', 'none', 'noone', 'nor', 'not', 'nothing', 'now',
                     'nowhere', 'of', 'off', 'often', 'on', 'once', 'one',
                     'only', 'onto', 'or', 'other', 'others', 'otherwise',
                     'our', 'ours', 'ourselves', 'out', 'over', 'own', 'part',
                     'per', 'perhaps', 'please', 'put', 'rather', 're', 'same',
                     'see', 'seem', 'seemed', 'seeming', 'seems', 'serious',
                     'several', 'she', 'should', 'show', 'side', 'since',
                     'sincere', 'six', 'sixty', 'so', 'some', 'somehow',
                     'someone', 'something', 'sometime', 'sometimes',
                     'somewhere', 'still', 'such', 'system', 'take', 'ten',
                     'than', 'that', 'the', 'their', 'them', 'themselves',
                     'then', 'thence', 'there', 'thereafter', 'thereby',
                     'therefore', 'therein', 'thereupon', 'these', 'they',
                     'thick', 'thin', 'third', 'this', 'those', 'though',
                     'three', 'through', 'throughout', 'thru', 'thus', 'to',
                     'together', 'too', 'top', 'toward', 'towards', 'twelve',
                     'twenty', 'two', 'un', 'under', 'until', 'up', 'upon',
                     'us', 'very', 'via', 'was', 'we', 'well', 'were', 'what',
                     'whatever', 'when', 'whence', 'whenever', 'where',
        'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon', 'wherever',
        'whether', 'which', 'while', 'whither', 'who', 'whoever', 'whole',
        'whom', 'whose', 'why', 'will', 'with', 'within', 'without', 'would',
        'yet', 'you', 'your', 'yours', 'yourself', 'yourselves']

    return [word for word in words if word not in stopwords]

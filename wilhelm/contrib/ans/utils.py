from __future__ import division

from apps.core.utils import strings 
from .conf import recall_f1_score_number_of_relevant_items as f1_recall_denominator

def f1score(true_recall_count,
            true_recall_rate,
            f1_recall_denominator):

    """Return the F1 score for a recall test.

    Returns:
        A float.

    """

    try:
        recall = min(1.0, true_recall_count/f1_recall_denominator)
        precision = true_recall_rate
        f1 = 2.0*recall*precision/float(recall+precision)
    except TypeError:
            f1 = None
    except ZeroDivisionError:
            f1 = 0.0

    return f1

  
def WordRecognitionTestStimuliCheck(memorandum, inwords, outwords):

    '''
    Take three lists of strings: memorandum, inwords, outwords.
    Check if all strings in inwords are in memorandum.
    Check if all strings in outwords are not in memorandum.
    Check if inwords and outwords are disjoint sets.

    '''

    inwords = set(inwords)
    outwords = set(outwords)
    memorandum = set(memorandum)


    # Are outwords and inwords distinct?
    inoutdisjoint = inwords.isdisjoint(outwords)

    # Are all inwords in the memoranda?
    insubsetmemo = inwords.issubset(memorandum)

    # Are no outwords in memoranda?
    outmemodisjoint = outwords.isdisjoint(memorandum)

    try:

        assert inoutdisjoint
        assert insubsetmemo
        assert outmemodisjoint

    except AssertionError:

        ErrMsgA = ErrMsgB = ErrMsgC = ''
        if not inoutdisjoint:
            ErrMsgA += 'The inwords and outwords are not disjoint:\n'
            ErrMsgA += 'The following words are in both in and outwords: '
            ErrMsgA += ','.join(inwords.intersection(outwords))

        if not insubsetmemo:
            ErrMsgB += 'The inwords are not all in the memorandum.\n'
            ErrMsgB += 'The following inwords are not in the memorandum: '
            ErrMsgB += ','.join(inwords.difference(memorandum))

        if not outmemodisjoint:
            ErrMsgC += 'Some outwords are in the memorandum.\n'
            ErrMsgC += 'The following outwords are in the memorandum: '
            ErrMsgC += ','.join(outwords.intersection(memorandum))

        raise AssertionError('\n\n'.join([ErrMsgA, ErrMsgB, ErrMsgC]))


def calculate_recall_rates(memoranda, recalled_words):

        recall_count = len(recalled_words)

        true_recalls = []
        false_recalls = []

        for word in recalled_words:

            word = word.lower()
            
            if word in memoranda:
                true_recalls.append(word)
            else:
                false_recalls.append(word)
            
        true_recall_count = len(true_recalls)
        false_recall_count = len(false_recalls)

        try:
            true_recall_rate = true_recall_count/recall_count
            true_recall_percentage = int(true_recall_rate * 100)
        except ZeroDivisionError:
            true_recall_rate = None
            true_recall_percentage = None

        try:
            false_recall_rate = false_recall_count/recall_count
            false_recall_percentage = int(false_recall_rate * 100)
        except ZeroDivisionError:
            false_recall_rate = None
            false_recall_percentage = None

        f1 = f1score(true_recall_count,
                     true_recall_rate,
                     f1_recall_denominator)

        summary = dict(true_recalls = true_recalls,
                       false_recalls = false_recalls,
                       true_recall_count = true_recall_count,
                       false_recall_count = false_recall_count,
                       recall_count = recall_count,
                       true_recall_rate = true_recall_rate,
                       f1 = f1,
                       true_recall_percentage = true_recall_percentage,
                       false_recall_percentage = false_recall_percentage,
                       false_recall_rate = false_recall_rate)

        return summary


def nonstopword_unique_tokens(words):

    return strings.rmstopwords(set(words))

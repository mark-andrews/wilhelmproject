from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import random
import numpy as np

#================================ End Imports ================================

def shuffle(sequence):

    '''
    Call random.shuffle, the in-place shuffle.
    '''

    random.shuffle(sequence)

def permutation(N):

    '''
    Return a permutation of the integers 0 to N-1.    
    '''
    return list(np.random.permutation(N))

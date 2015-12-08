'''
Utilities to extend docutils.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
from docutils import core

#================================ End Imports ================================


def rst2innerhtml(text):
    '''
    Given some rst text, process as html and return the body only.

    '''

    d = core.publish_parts(text, writer_name='html')
    return d['body']

from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging
import os

#=============================================================================
# Django imports.
#=============================================================================
from django.conf import settings

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils.docutils import rst2innerhtml
from apps.core.utils.django import http_response

#=============================================================================
# Other imports
#=============================================================================
import configobj

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

# ============================================================================
# ============================================================================
def welcome(request):
    '''
    The main landing page for the experiments website.
    '''

    welcome_info\
        = configobj.ConfigObj(os.path.join(settings.WILHELM_ROOT,
                                           'apps/front/flatfiles/welcome.cfg'))

    welcome_blurbs = []
    for welcome_blurb_key, welcome_blurb in welcome_info.iteritems():
        welcome_blurbs.append((welcome_blurb['title'],
                               rst2innerhtml(welcome_blurb['short-text']),
                              ))

    context = {'title': 'Cognition Experiments',
               'welcome_blurbs': welcome_blurbs}

    return http_response(request, 'front/welcome.html', context)

def blurb(request, blurb_type):
    '''
    The view for the blurb pages. These pages present general info about the
    site and their content is stored in text files as restructuredText.'''

    blurb_types = dict(about='about.cfg',
                       takingpart='takingpart.cfg',
                       privacy='privacy.cfg')

    _blurb = configobj.ConfigObj(os.path.join(settings.WILHELM_ROOT,
                                              'apps/front/flatfiles',
                                              blurb_types[blurb_type]))

    blurb = dict(title = _blurb['title'],
                 text = rst2innerhtml(_blurb['text']))
                                          
    context = {'title': 'Cognition Experiments',
               'blurb': blurb}

    return http_response(request, 'front/blurb.html', context)

def admin(request):
    # TODO (Sat 13 Dec 2014 19:47:07 GMT): Presumably this is broken.
    return http_response(request, 'administration/admin.html')

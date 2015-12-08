from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import logging

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.research import models
from apps.core.utils.django import http_response
from apps.core.utils.docutils import rst2innerhtml

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')


def listing(request):
    '''
    Return a page listing all available experiments.
    '''
    projects = models.Project.objects.all()

    project_list = []
    for project in projects:

        project_list.append( 
            dict(url = project.experiment.name,
                 name = project.experiment.class_name,
                 title = project.experiment.title,
                 blurb = rst2innerhtml(project.blurb))
        )

    context = dict(title = 'Experiment List',
                   projects = project_list)

    return http_response(request, 'research/listing.html', context)

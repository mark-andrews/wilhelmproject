from __future__ import absolute_import

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.archives import models
from apps.core.utils.django import http_response
from apps.core.utils.docutils import rst2innerhtml

#================================ End Imports ================================

def listing(request):
    '''
    Return a page listing all available experiments.
    '''
    experiments = models.Experiment.objects.filter(live=True)

    experiment_list = []
    for experiment in experiments:

        experiment_list.append( 
            dict(url = experiment.name,
                 name = experiment.class_name,
                 title = experiment.title,
                 blurb = rst2innerhtml(experiment.blurb))
        )

    context = dict(title = 'Experiment List',
                   experiments = experiment_list)

    return http_response(request, 'archives/listing.html', context)

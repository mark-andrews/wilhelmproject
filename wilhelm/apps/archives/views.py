from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging

#=============================================================================
# Django imports.
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.presenter.conf import PLAY_EXPERIMENT_ROOT
from apps.archives import models
from apps.core.utils.django import http_response
from apps.core.utils.docutils import rst2innerhtml

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

def get_experiment(experiment_name, live=True):

    """
    Get the experiment whose name is `experiment_name` and that is also live.

    """

    experiment_class_name = experiment_name.capitalize()

    experiments\
        = models.Experiment.objects.filter(class_name = experiment_class_name,
                                           live=live)

    if len(experiments) == 1:
        return experiments[0]
    elif len(experiments) > 1:
        raise MultipleObjectsReturned
    else:
        raise ObjectDoesNotExist

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
                   experiments = experiment_list,
                   PLAY_EXPERIMENT_ROOT = PLAY_EXPERIMENT_ROOT)

    return http_response(request, 'archives/listing.html', context)


def experiment_homepage(request, experiment_name):

    try:

        experiment = get_experiment(experiment_name, live=True)

        context\
            = dict(title = experiment.name,
                   PLAY_EXPERIMENT_ROOT = PLAY_EXPERIMENT_ROOT,
                   experiment_url = experiment.name,
                   experiment_name = experiment.class_name,
                   experiment_title = experiment.title,
                   experiment_blurb = rst2innerhtml(experiment.blurb)
        )

        return http_response(request, 
                             'archives/experiment_homepage.html', 
                             context)

    except ObjectDoesNotExist:
            
        error_msg\
            = "No page or experiment matching \"{0}\" could not be found.".format(experiment_name)

        logger.warning(error_msg)

        raise Http404(error_msg)

    except MultipleObjectsReturned:

        error_msg\
            = "Mutiple experiments with the name \"{0}\" were found.".format(experiment_name)

        logger.warning(error_msg)

        raise Http404(error_msg)

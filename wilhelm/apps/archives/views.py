from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
from collections import defaultdict
import logging

#=============================================================================
# Django imports.
#=============================================================================
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.presenter.conf import PLAY_EXPERIMENT_ROOT
from apps.presenter.utils.viewutils import user_not_authenticated

from apps.subjects.models import Subject
from apps.subjects.utils import wilhelmlogin
from apps.archives import models
from apps.archives.models import Experiment
from apps.subjects.utils import (get_subject_from_request,
                                 has_unlimited_experiment_attempts)
from apps.core.utils.django import http_response, push_redirection_url_stack
from apps.core.utils.strings import uid
from apps.core.utils.docutils import rst2innerhtml
from apps.sessions.models import ExperimentSession

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

def get_experiment(experiment_name, live=True):

    """
    Get the experiment whose name is `experiment_name` and that is also live.

    """

    experiment_class_name = experiment_name.capitalize()

    experiments\
        = Experiment.objects.filter(class_name = experiment_class_name,
                                           live=live)

    if len(experiments) == 1:
        return experiments[0]
    elif len(experiments) > 1:
        raise MultipleObjectsReturned
    else:
        raise ObjectDoesNotExist


def get_most_recent_attempt_status(experiment_sessions):

    most_recent_attempt = list(experiment_sessions)[-1]

    if most_recent_attempt.is_live:
        status = 'live'
    elif most_recent_attempt.is_paused:
        status = 'paused'
    elif most_recent_attempt.is_completed:
        status = 'completed'

    return status, most_recent_attempt.date_started, most_recent_attempt.date_completed


def get_experiment_context(request, experiment):

    experiment_context = dict(
        url = experiment.name,
        name = experiment.class_name,
        title = experiment.title,
        blurb = rst2innerhtml(experiment.blurb),
        single_attempt_only = experiment.single_attempt_only,
    )

    if request.user.is_authenticated():

        subject = get_subject_from_request(request)

        experiment_sessions\
            = ExperimentSession.objects.get_my_this_experiment_sessions(experiment,
                                                                        subject)

        if len(experiment_sessions) > 0:

            experiment_context['visited'] = True

            completions\
                = ExperimentSession.objects.get_my_completions(experiment,
                                                               subject)

            experiment_context['number_of_completions'] = completions

            if (has_unlimited_experiment_attempts(request)
                    or (completions < experiment.attempts)):

                experiment_context['attempts_remaining'] = True
                experiment_context['number_of_attempts_remaining']\
                    = experiment.attempts - completions
            else:
                experiment_context['attempts_remaining'] = False
                experiment_context['number_of_attempts_remaining'] = 0


            (experiment_context['most_recent_attempt_status'],
            experiment_context['date_started'],
            experiment_context['date_completed'])\
                = get_most_recent_attempt_status(experiment_sessions)

            print(get_most_recent_attempt_status(experiment_sessions))

        else:
            experiment_context['visited'] = False


    return experiment_context
 
def listing(request):
    '''
    Return a page listing all available experiments.
    '''

    experiments = Experiment.objects.filter(live=True)

    experiment_list = []
    for experiment in experiments:
        experiment_list.append(get_experiment_context(request, experiment))

    context = dict(title = 'Experiment List',
                   experiments = experiment_list,
                   PLAY_EXPERIMENT_ROOT = PLAY_EXPERIMENT_ROOT)

    return http_response(request, 'archives/listing.html', context)


def experiment_homepage(request, experiment_name, anonymous=False):

    

    try:

        experiment = get_experiment(experiment_name, live=True)

        experiment_context = get_experiment_context(request, experiment)

        context\
            = dict(title = experiment.name,
                   PLAY_EXPERIMENT_ROOT = PLAY_EXPERIMENT_ROOT,
                   experiment = experiment_context)

        print(context)
        if anonymous:
            context['PLAY_EXPERIMENT_ROOT']\
                = '/anonymous' + PLAY_EXPERIMENT_ROOT.strip('/') + '/'

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


def anonymous_experiment(request, experiment_name):

    password = 'anonymoususerpassword'+ uid(k=5)

    if user_not_authenticated(request):

        while True:
            proposed_username = 'anon' + uid(k=5)
            if not User.objects.filter(username = proposed_username):
                break

        user = User.objects.create_user(username = proposed_username,
                                        first_name = 'Participant',
                                        password = password)

        user.save()

        Subject.objects.create_subject(user)

        wilhelmlogin(request, proposed_username, password)

    return experiment_homepage(request, experiment_name, anonymous=True)

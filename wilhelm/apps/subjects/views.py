from __future__ import absolute_import, print_function

#=============================================================================
# Standard library imports.
#=============================================================================
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.http import Http404
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib.auth import logout

#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import conf
from .models import Subject
from .utils import (SignUpForm, 
                    LoginForm, 
                    ForgotPasswordForm,
                    dump_traceback,
                    DemographicsForm,
                    is_demo_account,
                    get_subject_from_request)
from apps.core.utils.django import (http_response,
                                    form_view,
                                    push_redirection_url_stack)
from apps.sessions.models import ExperimentSession
from apps.sessions.conf import status_completed
from apps.archives.models import Experiment
from apps.archives.views import get_most_recent_attempt_status
from apps.dataexport.utils import tojson
from apps.core.utils.django import http_redirect
from apps.subjects.utils import has_unlimited_experiment_attempts
from apps.core.utils.docutils import rst2innerhtml


#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

@login_required
def subject_initialization_routine(request):

    '''
    This is the gateway through which subject enter the website. It checks
    their demographic requirments.

    '''

    if is_demo_account(request):
        return http_redirect(request)

    else:

        subjects = Subject.objects.filter(user=request.user)

        try:
            if len(subjects) == 0:
                msg = 'A user with no subject persona should not be here.'
                logger.warning(msg)

                # TODO (Thu 26 Feb 2015 02:33:25 GMT): Raise a proper exception. 
                raise Exception(msg)

            elif len(subjects) > 1:

                # TODO (Sat 11 Jul 2015 16:06:44 BST): If we are
                # short-circuiting this method with the is_demo_account check
                # and redirect above, then this logic is probably obsolete or
                # unnecessary, right?

                try:

                    msg = 'A user with multiple non-temporary subject persona.'
                    assert all([subject.temp_subject for subject in subjects]), msg

                    context = dict(temp_user = True)
                    return http_response(request, 'subjects/profile.html', context)

                except AssertionError as e:
                    logger.warning(e.message)
                    raise 

            else:

                logger.info('Initialization of subject with unique subject account.')

                return getdemographicsview(request)

        except (Exception, AssertionError) as e:

            exception_details = dump_traceback()

            logger.warning('An exception: %s.' % e.message)
            logger.warning('Exception details: %s.' % exception_details)

def logoutview(request):

    if is_demo_account(request):
        temp_subject\
            = Subject.objects.get(uid = request.session['temp_subject_uid'])
        temp_subject.delete()
        del request.session['temp_subject_uid']

    logout(request)
    return HttpResponseRedirect('/')

def loginview(request, admin=False):

    if 'next' in request.GET:
        push_redirection_url_stack(request, request.GET['next'])


    # TODO (Thu 26 Feb 2015 00:07:10 GMT): Why are we doing @loginrequired?
    if not request.user.is_authenticated():

        if admin:
            template = 'administration/admin_login.html'
            title = 'Admin Login'
            login_title = 'Admin Login'
            login_url = '/adminlogin'
        else:
            template = 'subjects/member_login.html'
            title = 'Member Login'
            login_title = 'Member Login'
            login_url = '/login'

        context = {'title': title,
                   'no_show_login': True,
                   'username_placeholder': conf.username_placeholder,
                   'login_title': login_title}

        return form_view(request,
                         template=template,
                         context=context,
                         process=LoginForm.process,
                         prgobject_key='loginform_context',
                         url_on_valid = lambda: '/initialize',
                         url_on_invalid=lambda: login_url)
    else:

        return HttpResponseRedirect('/')

@login_required
def notifyme(request):

    subject = get_subject_from_request(request)

    if subject.has_notification_status:
        notifyme_placeholder = subject.notification_status
    else:
        notifyme_placeholder = conf.notifyme_placeholder

    context = dict(notifyme_placeholder = notifyme_placeholder)

    def process(request):
        notifyme_post = request.POST['notifyme']
        feedback = dict(notifyme_placeholder = notifyme_post)
        if notifyme_post in ('yes', 'no'):
            subject.set_notification_status(notifyme_post)
            return True, feedback
        else:
            return False, feedback

    return form_view(request,
                     template = 'subjects/notifications.html',
                     context=context,
                     process=process,
                     prgobject_key = 'handednessform_context',
                     url_on_valid = lambda: '/',
                     url_on_invalid = lambda: '/notifyme')

 
def forgotpasswordview(request):

    if not request.user.is_authenticated():

        context = {'title': 'Forgot Password',
                   'username_placeholder': conf.username_placeholder,
                   'forgot_your_password_title': conf.forgot_your_password_title}

        return form_view(request,
                        template='subjects/forgotpassword.html',
                        context=context,
                        process=ForgotPasswordForm.process,
                        prgobject_key='forgotpasswordform_context',
                        url_on_valid= lambda: '/forgotpassword',
                        url_on_invalid= lambda: '/forgotpassword')
    else:

        return HttpResponseRedirect('/')


def signupview(request):

    if not request.user.is_authenticated():

        context = {'minimal_password_length': conf.minimal_password_length,
                   'firstname_placeholder': conf.firstname_placeholder,
                   'username_placeholder': conf.username_placeholder,
                   'no_show_signup': True,
                   'title': 'Sign up'}

        return form_view(request,
                         template = 'subjects/signup.html',
                         context=context,
                         process=SignUpForm.process,
                         prgobject_key = 'signupform_context',
                         url_on_valid = lambda: '/initialize',
                         url_on_invalid = lambda: '/signup')
    else:

        return HttpResponseRedirect('/')

def profileview(request):

    if is_demo_account(request):
        return HttpResponseRedirect('/')

    else:
        user = request.user
        subject = Subject.objects.get(user=user)

        demographics = {}

        if subject.has_sex:
            demographics['sex'] = subject.sex

        if subject.has_dob:
            demographics['dob'] = subject.birthdate
            demographics['age'] = subject.age

        if subject.has_language:
            demographics['native_language'] = subject.native_language

        if subject.has_handedness:
            demographics['handedness'] = subject.handedness

        context = dict(demographics=demographics)

        return http_response(request, 'subjects/profile.html', context)

def getdemographicsview(request):

    '''
    The view for the demographic form submission page.
    '''
    
    demographic_templates = dict([
        ('Date_of_Birth', 'subjects/birthday.html'),
        ('Sex', 'subjects/sex.html'),
        ('Handedness', 'subjects/handedness.html'),
        ('Native_Language', 'subjects/native-language.html')
    ])

    subject = get_subject_from_request(request)
    
    required_variables\
        = [variable for (variable, required) in conf.demographic_variables\
           if required and not subject.has(variable)]

    placeholders\
        = {variable + '_placeholder': value for variable, value\
           in conf.demographic_variables_placeholders.items()\
           if variable in required_variables}

    templates\
        = [demographic_templates[variable] for variable in required_variables]

    if required_variables:

        context = dict(demographic_templates = templates)
        context.update(placeholders)
        
        logger.info(
            'Subject %s. Getting demographic variables: %s'\
            % (subject.user.username, ', '.join(required_variables))
        )
        
        process = lambda request: DemographicsForm.process(request, 
                                                           required_variables)

        return form_view(request,
                         template = 'subjects/demographicsform.html',
                         context=context,
                         process=process,
                         prgobject_key = 'demographicsform_context',
                         url_on_valid = lambda: http_redirect(request).url,
                         url_on_invalid = lambda: '/initialize')
    else:

        logger.info(
            'Subject %s. No required demographic variables.' % (subject.user.username)
        )
 
        return http_redirect(request)


def get_completed_experiment_sessions(request, experiment_name):

    """ Find all experiments session, with name `experiment_name`, that were
    completed by the subject in request.

    Return:
        A QuerySet of ExperimentSessions, reverse ordered by attempt.

    """

    subject = get_subject_from_request(request)

    experiments\
        = Experiment.objects.filter(class_name=experiment_name.capitalize())

    try:
        if len(experiments) == 1:
            experiment = experiments[0]
        elif len(experiments) > 1:
            raise MultipleObjectsReturned
        else:
            raise ObjectDoesNotExist

    except (MultipleObjectsReturned, ObjectDoesNotExist):
        raise Http404

    return ExperimentSession\
           .objects\
           .filter(subject=subject, experiment_version__experiment=experiment)\
           .order_by('-attempt')\
           .filter(status = status_completed)


@login_required
def experiment_feedback(request, experiment_name):

    """
    Return the subject's feedback for experiment `experiment_name`.

    If there is no feedback for that experiment, i.e., subject has not
    completed the experiment, then send them to a 'no feedback yet' page.

    """

    completed_experiment_sessions\
        = get_completed_experiment_sessions(request, experiment_name)

    if len(completed_experiment_sessions) == 0:

        return http_response(request, 
                             template='subjects/no_experiment_feedback.html', 
                             context=dict(experiment_name=experiment_name))

    else:
        completed_sessions_feedback\
            = [experiment_session.feedback() 
               for experiment_session in completed_experiment_sessions]

        context = dict(feedbacks=completed_sessions_feedback,
                       jsonfeedback=tojson(completed_sessions_feedback))
        
        # TODO (Tue 07 Jun 2016 16:19:56 BST): This is a hack. 
        # There should be a feedback template associated with this experiment, i.e.
        # at the Playlist level. That template should be used here.

        # TODO (Tue 07 Jun 2016 16:48:17 BST): This is an even bigger hack.
        # Here, we are doing special processing of the feedback for bartlett based
        # memory tests. But really, this should be done in a bartlett/views.py. 
        # Or just call template * context from the SessionPlaylist 
        if experiment_name in ('brisbane', 'malmo', 'quezon', 'lapaz'):

            template = 'bartlett/experiment_feedback.html'
            context = dict(feedback=completed_sessions_feedback[0],
                           jsonfeedback=tojson(completed_sessions_feedback))

        elif experiment_name == 'apia':

            template = 'ans/experiment_feedback.html'
            context = dict(feedback=completed_sessions_feedback[0],
                           jsonfeedback=tojson(completed_sessions_feedback))
         
        else:
            template = 'subjects/experiment_feedback.html'
            context = dict(feedbacks=completed_sessions_feedback,
                           jsonfeedback=tojson(completed_sessions_feedback))

        return http_response(request, template, context)

@login_required
def feedback(request):

    '''
    Render a feedback listing page for the Subject of the request.

    Returns:
        A http_response object with the 'subject/feedback.html' rendered to
        list out all completed experiments.


    '''

    subject = get_subject_from_request(request)


    # This will get a unique list of experiments that have been
    # *completed* by the subject.
    completed_experiments = []
    for experiment_session in ExperimentSession.objects.filter(subject=subject,
                                                               status=status_completed):
           completed_experiments.append(experiment_session.experiment_version.experiment)

    completed_experiments = set(completed_experiments)


    experiments = []
    for experiment in completed_experiments:

        experiment_context = dict(
            url = experiment.name,
            name = experiment.class_name,
            title = experiment.title,
            blurb = rst2innerhtml(experiment.blurb),
            single_attempt_only = experiment.single_attempt_only,
        )

        experiment_sessions\
            = ExperimentSession.objects.get_my_this_experiment_sessions(experiment,
                                                                        subject)

        completions = ExperimentSession.objects.get_my_completions(experiment,
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


        experiments.append(experiment_context)

    context = dict(experiments = experiments)

    return http_response(request, 'subjects/feedback.html', context)

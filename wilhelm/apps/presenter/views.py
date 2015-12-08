from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import json
import logging

#=============================================================================
# Django imports.
#=============================================================================
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.decorators.cache import never_cache, cache_control

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.archives.models import Experiment
from apps.core.utils import django

#=============================================================================
# Local (Wilhelm) imports.
#=============================================================================
from . import conf
from .utils import viewutils
from .utils.slidelauncher import SlideLauncherFactory
from .utils.slideviews import SlideViewFactory
from .utils.viewutils import (presenter_error_response, 
                              redirect_login_redirect,
                              user_not_authenticated)

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

def experiment_exists_or_404(experiment_name):
    
    """
    If `experiment_name` does not exist in Experiment model, raise 404.

    """

    try:
        Experiment.objects.get(class_name = experiment_name.capitalize())
    except ObjectDoesNotExist:
        raise Http404

    return True

def foobar(request):
    return experiment_launcher(request,'brisbane')

def try_experiment_launcher(request, experiment_name):

    """
    Check if `experiment_name` is a valid experiment name. If so, pass to
    experiment_launcher.

    """

    assert experiment_exists_or_404(experiment_name)
    
    return experiment_launcher(request, experiment_name)


def try_experiment(request, experiment_name, short_uid):

    """
    Check if `experiment_name` is a valid experiment name. If so, pass to
    experiment_launcher.

    """

    assert experiment_exists_or_404(experiment_name)

    return experiment(request, experiment_name, short_uid)


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def experiment_launcher(request, experiment_name):

    if user_not_authenticated(request):
        return redirect_login_redirect(request, '/' + experiment_name)

    else:
        try:
            launcher = SlideLauncherFactory.new(request, experiment_name)
        except AssertionError as e:
            return presenter_error_response(request, e.message)

        request.session['slide_to_be_launched_info_uid']\
            = launcher.get_slide_to_be_launched_info_uid()

        rendered_launcher = launcher.render()

        return HttpResponse(rendered_launcher)

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def experiment(request, experiment_name, short_uid):
    '''
    The main function to serve out the slide spa. While this function is called
    from the urls.py, it assumes that the experiment launcher has been called.

    If the experiment launcher has not been called, then hopefully an
    AssertionError will be raised and then the right experiment_launcher will
    be called.

    '''

    if user_not_authenticated(request):
        return redirect_login_redirect(request, '/' + experiment_name)

    else:

        try:
            slideview = SlideViewFactory.new(request, 
                                             experiment_name, 
                                             short_uid)
        except AssertionError:
            return experiment_launcher(request, experiment_name)

        slide = slideview.get_slide()

        assert slideview.live_session.uid == slide.live_session.uid

        rendered_slide = slide.render()

        return HttpResponse(rendered_slide)

#############################################
############## Gateway Views ################
#############################################

def get_live_experiment(request):
    '''
    A wrapper for viewutils.LiveExperiment(request).  Most (all) gateway
    functions call this to do some checking and general code.
    '''

    assert request.is_ajax(), 'Not an ajax request.'

    live_experiment = viewutils.LiveExperiment(request)

    # Get the slide's uid
    get_or_post = getattr(request, request.method)
    ping_uid = get_or_post.get('ping_uid', None)

    assert ping_uid == live_experiment.live_session.nowplaying_ping_uid,\
        (ping_uid, live_experiment.live_session.nowplaying_ping_uid)

    return live_experiment

def ping_gateway(request):
    ''' 
    A function to handle GET and POST requests concerning the stay_alive value.
    GET requests:
    The slide-spa in the browser periodically sends GET requests to see if it
    should stay alive. If it is returned a stay_alive = False, the slide-spa
    shuts down.
    POST request:
    The slide-spa can send a POST request to tell the live_session to stay
    alive. This is particularly used in the case where the live_session sends a
    keep_alive=false signal, but the user on the browser indicates that the
    slide should continue when presented with a time-out countdown.
    '''

    live_experiment = get_live_experiment(request)

    if request.session.get(conf.live_experiment, None):

        if request.method == 'GET':

            # The keep_alive signal is True  if the live_session has a keep
            # alive value of True

            if live_experiment.live_session.keep_alive:
                keep_alive = True
            else:
                keep_alive = False
    
            live_experiment.live_session.stamp_last_ping_time()

            keep_alive_json = json.dumps(dict(keep_alive = keep_alive))


        elif request.method == 'POST':

            if request.POST.get('keep_alive', None):
                
                keep_alive = json.loads(request.POST['keep_alive'])

                if keep_alive:
                    live_experiment.live_session.set_keep_alive()
                else:
                    live_experiment.hangup()
            
            live_experiment.live_session.stamp_last_ping_time()

            keep_alive_json = json.dumps(dict(keep_alive = keep_alive))

        return django.jsonResponse(keep_alive_json)

def widget_gateway(request, widget_name):
    '''
    When data is get-ed or post-ed to widget gateway, this function is called.
    All information get shipped off to the nowplaying slide.
    '''

    live_experiment = get_live_experiment(request)

    nowplaying = live_experiment.get_nowplaying()

    widget = nowplaying.get_session_widget(widget_name)

    if widget:

        live_experiment.live_session.stamp_time()

        if request.method == 'GET':
            logger.debug('Widget GET request')
            data = widget.get()
            logger.debug('Data being GETed is: %s.' % data)
            return django.jsonResponse(json.dumps(data))

        elif request.method == 'POST':
            logger.debug('Widget POST request')
            feedback = widget.post(request.POST)
            feedback = json.dumps(feedback)
            logger.debug('Data being POSTed is: %s.' % feedback)
            return django.jsonResponse(feedback)

def hangup_nowplaying_gateway(request):
    '''
    When a slide comes to the end, it sends a signal to tell the server to
    hangup that slide. 
    We try to process all results in the slide, push the results onto the
    playlist and 
    '''

    live_experiment = get_live_experiment(request)

    if request.method == 'POST':

        is_hangup = json.loads(request.POST.get('is_hangup', None))
        if is_hangup:
            live_experiment.process_nowplaying_results()
            live_experiment.hangup_nowplaying()

            data = json.dumps({'is_hangup': True,
                               'experiment_uri': '/'+ live_experiment.name})

        else:
            data = json.dumps({'is_hangup': False})

        return django.jsonResponse(data)

def hangup_playlist_gateway(request):
    '''
    When we get to the end of a slide, we are by default presented with a pause
    or continue page. Or, if the slide is the last slide in the playlist, we
    get a stop playlist page. 
    The pause/continue/stop actions sent by ajax calls are processed here.
    '''

    live_experiment = get_live_experiment(request)

    if request.method == 'POST':

        if request.POST.has_key('next_playlist_action'):

            if 'pause_playlist' in request.POST['next_playlist_action']:
                live_experiment.hangup(status='pause')
                next_uri = conf.default_url 

            elif 'stop_playlist' in request.POST['next_playlist_action']:
                live_experiment.hangup(status='completed')
                next_uri = conf.default_url 

            elif 'get_playlist_feedback' in request.POST['next_playlist_action']:
                live_experiment.hangup(status='completed')
                next_uri = conf.feedback_uri + '/' + live_experiment.experiment.name

            return django.jsonResponse(json.dumps({'next_uri': next_uri}))

#############################################################
#############################################################

from django.conf.urls import url, include

experiment_name_regex = r'[a-zA-Z0-9]+'

# TODO (Sat 30 Aug 2014 14:03:47 BST): Shouldn't we put the presenter based
# urls inside apps.presenter.urls?

import apps.front.views
import apps.archives.views
import apps.subjects.views
import apps.presenter.views

from apps.presenter.conf import PLAY_EXPERIMENT_ROOT
PLAY_EXPERIMENT_ROOT = PLAY_EXPERIMENT_ROOT.strip('/')

urlpatterns = [

    #########
    # Front #
    #########
    url(r'^$', apps.front.views.welcome, name='homepage'),
    url(r'(?P<blurb_type>about|privacy|takingpart)', apps.front.views.blurb),

    ############
    # Archives #
    ############
    url(r'^experiments[/]*$', apps.archives.views.listing),
    url(r'^listing$', apps.archives.views.listing),
    url(r'^experiments/(?P<experiment_name>'+experiment_name_regex+')[/]*$', apps.archives.views.experiment_homepage),

    #=========================================================================
    # Social media logins
    #=========================================================================
    url('^socialmedia/', 
        include('social.apps.django_app.urls', namespace='social')
    ),

    #=========================================================================
    # Subjects
    #=========================================================================
    url(r'^login$', apps.subjects.views.loginview, {'admin': False}),
    url(r'^logout$', apps.subjects.views.logoutview),
    url(r'^forgotpassword$', apps.subjects.views.forgotpasswordview),
    url(r'^signup$', apps.subjects.views.signupview),
    url(r'^notifications$', apps.subjects.views.notifyme),
    url(r'^profile[/]*$', apps.subjects.views.profileview),
    url('^initialize[/]*$', apps.subjects.views.subject_initialization_routine),
    url(r'^feedback/(?P<experiment_name>'+experiment_name_regex+')$', 
        apps.subjects.views.experiment_feedback),
    url(r'^feedback[/]*$', apps.subjects.views.feedback),


    #=========================================================================
    # Administration
    #=========================================================================
    url(r'^adminlogin$', apps.subjects.views.loginview, {'admin': True}),
    url(r'^admin$', apps.front.views.admin),

    #############
    # Presenter #
    #############
    url(r'^hangup_nowplaying$', 
        apps.presenter.views.hangup_nowplaying_gateway),
    url(r'^hangup_playlist$', 
        apps.presenter.views.hangup_playlist_gateway),
    url(r'^hangup_playlist$', 
        apps.presenter.views.hangup_playlist_gateway),
    url(r'^widget_gateway/(?P<widget_name>.*)/$', apps.presenter.views.widget_gateway),
    url(r'^ping_gateway$', apps.presenter.views.ping_gateway),

    #############################
    # Match playing experiments #
    #############################
    url(r'^' + PLAY_EXPERIMENT_ROOT + '/(?P<experiment_name>'+experiment_name_regex+')[/]*$', apps.presenter.views.try_experiment_launcher),
    url(r'^' + PLAY_EXPERIMENT_ROOT + '/(?P<experiment_name>'+experiment_name_regex+')/(?P<short_uid>[0-9a-f]{7})[/]*$', apps.presenter.views.try_experiment),

    # Get rid of this hack and make a shortener!# TODO (Tue 12 Jul 2016 00:56:13 BST):  
    url(r'^alapaz[/]*$', apps.archives.views.anonymous_lapaz),
    url(r'^amalmo[/]*$', apps.archives.views.anonymous_malmo),
    url(r'^abrisbane[/]*$', apps.archives.views.anonymous_brisbane),

    ##########################
    # Anonymous experiments
    ##########################
    url(r'^anonymous/(?P<experiment_name>'+experiment_name_regex+')[/]*$', apps.archives.views.anonymous_experiment),
    url(r'^anonymous' + PLAY_EXPERIMENT_ROOT + '/(?P<experiment_name>'+experiment_name_regex+')[/]*$',
        apps.presenter.views.anonymous_experiment_prelaunch),

    # Put this last!
    ##########################
    # Match experiment names #
    ##########################
    url(r'^(?P<experiment_name>'+experiment_name_regex+')[/]*$', apps.archives.views.experiment_homepage),
]

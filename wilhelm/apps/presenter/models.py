'''
Models for the presenter app.
'''

from __future__ import absolute_import

#=============================================================================
# Stanard library imports.
#=============================================================================
from collections import OrderedDict
import logging
import json
import os

#=============================================================================
# Third party imports.
#=============================================================================
from jsonfield import JSONField
from django_user_agents.utils import get_user_agent

#=============================================================================
# Django imports.
#=============================================================================
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import conf
from apps.core.utils import django, datetime, sys
from apps.sessions import models as sessions_models
from apps.archives import models as archives_models
from apps.dataexport.utils import safe_export_data
from apps.presenter.utils.utils import get_ip_address, get_geoip_info

#================================ End Imports ================================


logger = logging.getLogger('wilhelm')

#=============================================================================
# Presenter models.
#=============================================================================
class SlideToBeLaunchedInfo(models.Model):
    '''
    When a subject requests an experiment, they first receive a "launcher". The
    launcher will provide them with some information about the next slide, etc.
    The information relevant to the slide-to-be-launched is stored here.
    '''

    uid = models.CharField(primary_key=True,
                           max_length=settings.UID_LENGTH)

    experiment = models.ForeignKey(archives_models.Experiment)
    ping_uid = models.CharField(max_length=settings.UID_LENGTH,
                                null=True,
                                primary_key=False)

    slideview_type = models.CharField(max_length=25,
                                      choices = conf.slideview_types
                                      )

    slideview_kwargs = JSONField(null=True)

    @classmethod
    def new(cls,
            experiment, 
            ping_uid, 
            slideview_type, 
            **slideview_kwargs):

        try:

            slide_to_be_launched\
                = cls.objects.select_related().get(experiment = experiment,
                                  ping_uid = ping_uid,
                                  slideview_type = slideview_type,
                                  slideview_kwargs = slideview_kwargs)

        except ObjectDoesNotExist:


            slide_to_be_launched\
                = cls.objects.create(uid = django.uid(),
                                     experiment = experiment,
                                     ping_uid = ping_uid, 
                                     slideview_type = slideview_type,
                                     slideview_kwargs=slideview_kwargs)


        return slide_to_be_launched

    @property
    def name(self): 
        return self.experiment.name

    @property
    def ping_uid_short(self):
        return self.ping_uid[:settings.UID_SHORT_LENGTH]


class LiveExperimentSessionManager(models.Manager):

    def get_live_sessions(self, subject):
        ''' Return the experiment sessions belonging to the subject who
        corresponds to the subject `subject`. '''
        return self.filter(experiment_session__subject = subject,
                           alive = True)

    def is_some_session_live(self, subject):
        '''
        If `subject` has any experiment live somewhere, then return True, else
        return False.
        '''
        if len(self.get_live_sessions(subject=subject)):
            return True
        else:
            return False

    def data_export(self, experiment_session):

        return [live_session.data_export() 
                for live_session in LiveExperimentSession\
                .objects.filter(experiment_session=experiment_session)]

class LiveExperimentSession(models.Model):

    '''
    A live experiment is an experiment now running in a browser session.
    The client's browser will be sending a ping every few seconds.
    '''
    uid = models.CharField(primary_key=True,
                           max_length=settings.UID_LENGTH)

    experiment_session = models.ForeignKey(sessions_models.ExperimentSession,
                                           null=True)
    date_created = models.DateTimeField(null=True)
    last_activity = models.DateTimeField(null=True)
    last_ping = models.DateTimeField(null=True)
    nowplaying_ping_uid = models.CharField(primary_key=False, 
                                           max_length=settings.UID_LENGTH,
                                           unique=True,
                                           null=True,
                                           blank=True)
    
    keep_alive = models.BooleanField(default=True)
    is_nowplaying = models.BooleanField(default=False)

    alive = models.BooleanField(default=False)

    objects = LiveExperimentSessionManager()

    #=============================================================================
    # User agent information
    #=============================================================================
    ua_string = models.TextField(null=True)
    ua_string_pp = models.TextField(null=True)
    ua_browser = models.TextField(null=True)
    ua_browser_version = models.TextField(null=True)
    ua_os = models.TextField(null=True)
    ua_os_version = models.TextField(null=True)
    ua_device = models.TextField(null=True)
    ua_is_mobile = models.NullBooleanField()
    ua_is_tablet = models.NullBooleanField()
    ua_is_touch_capable = models.NullBooleanField()
    ua_is_pc = models.NullBooleanField()
    ua_is_bot = models.NullBooleanField()

    #=============================================================================
    # Ip and geo-IP information
    #=============================================================================
    ip_address = models.TextField(null=True)
    city = models.TextField(null=True)
    country_name = models.TextField(null=True)
    country_code = models.TextField(null=True)
    country_code_alt = models.TextField(null=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)

    platform_info = JSONField(null=True)
    python_info = JSONField(null=True)
    pip_info = JSONField(null=True)
    wilhelm_info = JSONField(null=True)

    @classmethod
    def new(cls, experiment_session, request=None):

        now = datetime.now()

        live_experiment_session\
            =  cls.objects.create(uid=django.uid(),
                                  experiment_session = experiment_session,
                                  alive = True,
                                  date_created = now)

        live_experiment_session.experiment_session.make_live(now)

        if request:
            live_experiment_session.set_user_agent_info(request)
            live_experiment_session.set_ip_geoip_info(request)

        live_experiment_session.set_server_info()

        return live_experiment_session

    @property
    def name(self):

        '''
        Return the name of the experiment that is live in this session.
        '''

        return self.experiment_session.name

    @property
    def nowplaying_ping_uid_short(self):
        return self.nowplaying_ping_uid[:settings.UID_SHORT_LENGTH]

    def pseudo_delete(self):

        """
        We do not want to delete live_sessions, but we want to distinguish
        between actually live and no longer live.

        """

        logger.debug('Setting live_sessions to alive=False')

        self.alive = False
        self.save()

    def stamp_last_ping_time(self):

        '''Stamp last_ping as now.'''

        now = datetime.now()
        self.last_ping = now
        self.save()

    def stamp_time(self):

        '''Stamp last_activity as now. Sync with the experiment session.'''

        now = datetime.now()
        self.last_activity = now
        self.save()
        self.experiment_session.stamp_time(now)

    def set_keep_alive(self):

        ''' Keep the live session alive. '''

        self.keep_alive = True
        self.stamp_time()

    def hangup_nowplaying(self):

        ''' When we hang up a slide, we must None-ify the nowplaying file,
        slide uid and set is_nowplaying to False.
        '''

        self.experiment_session.hangup_nowplaying()

        self.nowplaying_ping_uid = None
        self.is_nowplaying = False
        self.stamp_time()

    def iterate_playlist(self, ping_uid):
        '''
        Iterate the playlist, getting the next slide and returning it. 
        The uid for the slide will be set to ping_uid. This will be an
        attribute of the slide itself, and also saved in the this live session
        model.

        The playlist is a pickled object. We want to iterate it here, but this
        requires taking it out of the db, iterating it, and then putting it
        back in to the db.

        '''

        if self.is_nowplaying:
            # FIXME
            # This will break because there is no such thing as
            # NowPlayingError.
            raise NowPlayingError(self.experiment_name)
        else:

            session_slide = self.experiment_session.iterate_playlist()
            session_slide.set_ping_uid(ping_uid) 

            self.set_nowplaying(ping_uid)

            return session_slide 

    def get_nowplaying(self):
        return self.experiment_session.get_nowplaying()

    def set_nowplaying(self, ping_uid):
        '''
        Set slide to be nowplaying. We set the live_session to be
        is_nowplaying. Also, when we set a slide to nowplaying, we also pickle
        it for safe keeping.
        '''

        self.nowplaying_ping_uid = ping_uid
        self.is_nowplaying = True 
        self.stamp_time()    

    def data_export(self):

        export_dict = OrderedDict()

        export_dict['uid'] = self.uid
        export_dict['Initiated'] = self.date_created
        export_dict['Server'] = self.get_server_info()
        export_dict['Client'] = self.get_user_agent_info()
        export_dict['GeoIP'] = self.get_ip_geoip_info()

        return export_dict

    def get_server_info(self):

        export_dict = OrderedDict()

        for key, f in [
                ('Platform', lambda: OrderedDict(self.platform_info)), # Remove this.
                ('Python', lambda: OrderedDict(self.python_info)),
                ('Pip requirements', lambda: self.pip_info),
                ('Wilhelm version', lambda: self.wilhelm_info),
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict


    def get_ip_geoip_info(self):

        export_dict = OrderedDict()

        for key, f in [
                #('IP address', lambda: self.ip_address), # Remove this.
                ('city', lambda: self.city),
                ('country', lambda: self.country_name),
                ('country code', lambda: self.country_code),
                ('country code alt', lambda: self.country_code_alt),
                ('longitude', lambda: self.longitude), # Remove this.
                ('latitude', lambda: self.latitude), # Remove this.
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def get_user_agent_info(self):

        def browser(self):

            if self.ua_browser is None:
                return None

            if self.ua_browser_version is not None:
                return self.ua_browser + ' ' + self.ua_browser_version

        def the_os(self):

            if self.ua_os is None:
                return None

            if self.ua_os_version is not None:
                return self.ua_os + ' ' + self.ua_os_version

        export_dict = OrderedDict()

        for key, f in [
                ('user-agent', lambda: self.ua_string_pp),
                ('user-agent string', lambda: self.ua_string),
                ('browser', lambda: browser(self)),
                ('operating system', lambda: the_os(self)),
                ('device', lambda: self.ua_device),
                ('is_mobile', lambda: self.ua_is_mobile),
                ('is_tablet', lambda: self.ua_is_tablet),
                ('is_touch_capable', lambda: self.ua_is_touch_capable),
                ('is_pc', lambda: self.ua_is_pc),
                ('is_bot', lambda: self.ua_is_bot),
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def set_server_info(self):


        try:
            self.platform_info = sys.get_platform_info()
            self.save()
        except Exception as e:
            logger.warning('Could not get platform info: %s.' % e.message)

        try:
            self.python_info = sys.get_python_info()
            self.save()
        except Exception as e:
            logger.warning('Could not get python info: %s.' % e.message)

        try:
            self.pip_info = sys.get_pip_requirements()
            self.save()
        except Exception as e:
            logger.warning('Could not get Pip requirements: %s.' % e.message)

        try:
            self.wilhelm_info = settings.WILHELM_VERSION
            self.save()
        except Exception as e:
            logger.warning('Could not get Wilhelm info: %s.' % e.message)
            logger.warning(os.environ.keys())
            logger.warning(os.environ['DJANGO_SETTINGS_MODULE'])



    def set_ip_geoip_info(self, request):

        ip_address = get_ip_address(request)

        if ip_address:
            logger.info('Client IP address is %s.' % ip_address)
        else:
            logger.warning('Client IP address could not be determined.')

        self.ip_address = ip_address

        geoip_info = get_geoip_info(ip_address)

        for key in geoip_info:

            try:
                setattr(self, key, geoip_info[key])
            except Exception as e:
                exception_type = e.__class__.__name__
                logger.warning(
                    'Could not assign geoip info %s. Exception %s. Msg %s.'\
                    % (key, exception_type, e.message))

        self.save()

    def set_user_agent_info(self, request):

        try:
            user_agent = get_user_agent(request)
        except:
            logger.warning("Could not get user agent info.")

        try:
            self.ua_string = user_agent.ua_string
        except:
            logger.warning("Could not get user agent info: ua_sting")

        try:
            self.ua_string_pp = str(user_agent)
        except:
            logger.warning("Could not get user agent info: str(user_agent)")

        try:
            self.ua_browser = user_agent.browser.family
        except:
            logger.warning("Could not get user agent info: browser family")

        try:
            self.ua_browser_version = user_agent.browser.version_string
        except:
            logger.warning("Could not get user agent info: browser version")

        try:
            self.ua_os = user_agent.os.family
        except:
            logger.warning("Could not get user agent info: OS family")

        try:
            self.ua_os_version = user_agent.os.version_string
        except:
            logger.warning("Could not get user agent info: OS version")

        try:
            self.ua_device = user_agent.device.family
        except:
            logger.warning("Could not get user agent info: Device")

        try:
            self.ua_is_mobile = user_agent.is_mobile
        except:
            logger.warning("Could not get user agent info: is_mobile")

        try:
            self.ua_is_tablet = user_agent.is_tablet
        except:
            logger.warning("Could not get user agent info: is_tablet")

        try:
            self.ua_is_touch_capable = user_agent.is_touch_capable
        except:
            logger.warning("Could not get user agent info: is_touch_capable")

        try:
            self.ua_is_pc = user_agent.is_pc
        except:
            logger.warning("Could not get user agent info: is_pc")

        try:
            self.ua_is_bot = user_agent.is_bot
        except:
            logger.warning("Could not get user agent info: is_bot")

        self.save()

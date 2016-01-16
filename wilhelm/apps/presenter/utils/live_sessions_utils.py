from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import datetime
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.presenter.models import LiveExperimentSession
from apps.presenter import conf
from apps.core.utils import strings

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

def get_user_browser_sessions(user, live_session):

    '''Get the browser session belonging to user that points to
    live_session.'''

    for session in Session.objects.all():
        _session = session.get_decoded()
        uid = _session.get('_auth_user_id')

        try:

            if User.objects.get(pk=uid) == user:
                live_experiment = _session.get('live_experiment')
                if live_experiment and live_session.pk == live_experiment:
                    return session

        except ObjectDoesNotExist:
            pass

    logger.critical('User %s not found in Sessions.' % user)

def del_browser_live_session_store(browser_session):

    try:
        if browser_session:

            browser_session_store\
                = SessionStore(session_key=browser_session.session_key)
            browser_session_store['live_experiment'] = None
            del browser_session_store['live_experiment']
            browser_session_store.save()

            logger.debug('The purger has deleted the browser live session store.')

            return True
    except Exception as e:

        logger.warning('Failed to delete browser live session store: %s.' % e.message)


def flag_stale_live_sessions(live_session_keep_alive_duration=None):

    '''
    If last_activity on each live_session is older than
    live_session_keep_alive_duration, then set live_session.keep_alive to
    False.
    '''

    logger.debug('Flag any stale live sessions.')

    if live_session_keep_alive_duration is None:
        live_session_keep_alive_duration = conf.live_session_keep_alive_duration 

    for live_session in LiveExperimentSession.objects.filter(alive=True):

        last_activity_or_date_created\
            = live_session.last_activity or live_session.date_created

        try:
            d = datetime.datetime.now() - last_activity_or_date_created
            if d.total_seconds() > live_session_keep_alive_duration: 
                live_session.keep_alive = False
                live_session.save()
                logger.info(
                    'Flagging live_session %s for deletion.' % live_session.uid
                )

        except TypeError as e:

            message = strings.fill(''' Could not calculate time since
                                   live_session last_activity or date_created.
                                   ''')

            message = '\n'.join([message, 'Error message: ' + e.message])

            logger.warning(message)


def purge_flagged_live_sessions():

    """
    Find live sessions that are alive and flagged for (pseudo) deletion and
    then (pseudo) delete them.

    """


    logger.debug('Purge any stale live sessions that have been flagged.')

    for live_session in LiveExperimentSession.objects.filter(alive=True,
                                                             keep_alive=False):

        logger.debug('Trying to clean shutdown live_session: %s. ' % live_session.uid)

        experiment_session = live_session.experiment_session
        user = experiment_session.subject.user


        try:

            last_ping_or_date_created\
                = live_session.last_ping or live_session.date_created

            d = datetime.datetime.now() - last_ping_or_date_created

            if d.total_seconds() > conf.ping_grace_period:
     
                live_session.pseudo_delete()
                logger.debug('The purger has deleted live_session %s.' % live_session.uid)
                experiment_session.hangup(status='pause')
                logger.debug('The purger has hung-up experiment session %s.' % experiment_session.uid)

                browser_session = get_user_browser_sessions(user, live_session)
                del_browser_live_session_store(browser_session)
 
        except Exception as e:
            logger.warning('Something went wrong with the live session purge: %s.' % e.message)



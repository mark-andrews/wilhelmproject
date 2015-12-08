from __future__ import absolute_import

#=============================================================================
# Third party imports
#=============================================================================
import configobj
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.archives.models import Experiment
from apps.research import models as research_models

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

class Command(BaseCommand):

    args = 'experiments.cfg'
    help = 'Set which experiments are live; set their blurbs.'

    def handle(self, *args, **options):

        try:

            for arg in args:

                experiment_config = configobj.ConfigObj(arg)

                for experiment_name, experiment_settings in experiment_config.items():

                    try:
                        experiment = Experiment.objects.get(class_name=experiment_name)
                        #for key, values in experiment_settings.items():

                        if 'live' in experiment_settings:
                            experiment.live = bool(experiment_settings['live'])


                        if 'title' in experiment_settings:
                            experiment.title = experiment_settings['title']

                        if 'blurb' in experiment_settings:
                            experiment.blurb = experiment_settings['blurb']

                        if 'research_blurb' in experiment_settings:

                            project, _new\
                                = research_models.Project.objects.get_or_create(experiment=experiment)

                            project.blurb\
                                = experiment_settings['research_blurb']

                            project.save()

                        experiment.save()

                    except ObjectDoesNotExist as e:
                        # TODO (Tue 02 Dec 2014 07:37:54 GMT): Log this as a
                        # warning.
                        print(e)

                    except Exception as e:
                        print(e)

        except Exception as e:

            CommandError('Set experiments live failed: %s' % e.message)

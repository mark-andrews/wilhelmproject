from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
from collections import OrderedDict
import logging
import tempfile
import os

#=============================================================================
# Third party imports
#=============================================================================
from jsonfield import JSONField

#=============================================================================
# Django imports
#=============================================================================
from django.conf import settings
from django.db import models

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils import django, datetime
from apps.archives.models import Experiment
from apps.sessions.models import ExperimentSession

#=============================================================================
# Local imports 
#=============================================================================
from . import conf
from . import utils

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

checksums_to_dict = lambda checksums: dict(map(tuple, checksums))

def export_experiment(experiment, filename = 'data.json', tojson=True):

    export_dict = experiment.data_export()
    export_dict['ExperimentVersions'] = []

    for experiment_version in experiment.get_all_versions():

        experiment_version_export_dict = experiment_version.data_export()
        experiment_version_export_dict['Sessions']\
            = ExperimentSession.objects.data_export(experiment_version)

        export_dict['ExperimentVersions'].append(
            experiment_version_export_dict
        )

    if tojson:

        tmpdir = tempfile.mkdtemp()
        tmpfilename = os.path.join(tmpdir, filename)
        tmpfile = open(tmpfilename, 'w')
        tmpfile.write(utils.tojson(export_dict))
        tmpfile.close()
        os.chmod(tmpfilename, 0644)

        return tmpdir
    else:
        return export_dict

class ExperimentDataExportManager(models.Manager):

    def most_recent_entry(self, experiment):

        previous_entries\
            = self.filter(experiment=experiment).order_by('-datetime')

        if previous_entries:
            return previous_entries[0]


    def release(self, new_data_only=True):
        for experiment in Experiment.objects.all():
            ExperimentDataExport.release(experiment,
                                         new_data_only=new_data_only)


shorten_uid = lambda uid: uid[:settings.UID_SHORT_LENGTH]


class ExperimentDataExport(models.Model):

    uid = models.CharField(max_length=settings.UID_LENGTH,
                           primary_key=True)

    short_uid = models.CharField(max_length=settings.UID_SHORT_LENGTH,
                                 unique=True,
                                 null=True)

    experiment = models.ForeignKey(Experiment, null=True)
    datetime = models.DateTimeField(null=True)
    filename = models.CharField(max_length=100, null=True)
    attachment_filename = models.CharField(max_length=100, null=True)
    checksums = JSONField(null=True)
    filesize = models.CharField(null=True, max_length=100)

    objects = ExperimentDataExportManager()

    @classmethod
    def release(cls, experiment, new_data_only=True):

        try:

            exported_data_tmpdir = export_experiment(experiment)

            datetime_now = datetime.now()

            existing_short_uids\
                = [exp_data_export.uid[:settings.UID_SHORT_LENGTH]
                    for exp_data_export in cls.objects.all()]

            while True:
                uid = django.uid()
                short_uid = uid[:settings.UID_SHORT_LENGTH]

                if not (short_uid in existing_short_uids):
                    break


            label = utils.make_release_label(experiment.name, 
                                             datetime_now, 
                                             uid)
            
            experiment_url = settings.WWWURL + '/' + experiment.name,

            readme = utils.make_readme(conf.readme_template,
                                       experiment.name,
                                       experiment_url,
                                       uid,
                                       short_uid,
                                       datetime_now)

            license\
                = conf.odbl_license_template\
                .strip().format(DATA_NAME='data-set', UID=short_uid) + '\n'

            boilerplates = [
                (conf.readme_txt, readme),
                (conf.license_txt, license)
            ]

            tarball_filename, checksums, tarball_filesize\
                = utils.make_tarball(exported_data_tmpdir,
                                     boilerplates,
                                     label,
                                     compression_method=conf.tarball_compression_method,
                                     checksum_filename=conf.tarball_checksum)

            attachment_filename\
                = shorten_uid(uid) + '.tar.' + conf.tarball_compression_method

            create_new_data_export_instance\
                = lambda: cls.objects.create(uid = uid,
                                             short_uid = shorten_uid(uid),
                                             attachment_filename = attachment_filename, 
                                             experiment = experiment,
                                             datetime = datetime_now,
                                             checksums = checksums,
                                             filename = tarball_filename,
                                             filesize = tarball_filesize)

            if not new_data_only:
                create_new_data_export_instance()

            else:

                most_recent_data = cls.objects.most_recent_entry(experiment)

                if most_recent_data:

                    if checksums_to_dict(checksums) == checksums_to_dict(most_recent_data.checksums):

                        msg = 'Not exporting data for %s. New data identical to data previously collected at %s.'

                        logger.info(msg % (experiment.name,
                                           most_recent_data.datetime.strftime(conf.isoformat))
                                     )
                    else:
                                                  
                        create_new_data_export_instance()
                else:
                    create_new_data_export_instance()

        except Exception as e:
            exception_msg = 'Could not export data from experiment %s. %s: %s'
            logger.warning(exception_msg % (experiment.name, 
                                            e.__class__.__name__,
                                            e.message))

    @property
    def permalink(self):
        return settings.DATA_PERMALINK_ROOT + self.short_uid

    @property
    def filepath(self):
        return os.path.join(settings.DATA_ARCHIVES_CACHE,
                            self.filename)

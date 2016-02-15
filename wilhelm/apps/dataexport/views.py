from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import logging

#=============================================================================
# Third party imports
#=============================================================================
from sendfile import sendfile

#=============================================================================
# Django imports
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.presenter.conf import PLAY_EXPERIMENT_ROOT
from apps.dataexport import models
from apps.core.utils.django import http_response

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

def archive_download(request, archive_uid=None):

    try:

        archive\
            = models.ExperimentDataExport.objects.get(short_uid=archive_uid)


        return sendfile(request, 
                        filename=archive.filepath,
                        mimetype='application/x-tar',
                        attachment=True,
                        attachment_filename=archive.attachment_filename)


    except ObjectDoesNotExist as e:
        raise Http404(
            "data archive {archive_name} does not exist.".format(archive_uid)
        )
    except MultipleObjectsReturned as e:

        logger.warning('Multiple objects returned: %s' % e.message)
        raise Http404(
            "Can not return data archive {archive_name}.".format(archive_uid)
        )


def archive_listing(request):
    '''
    Return a page listing all available experiments.
    '''

    exports = models.ExperimentDataExport.objects.all()

    export_list = []
    for export in exports:

        export_list.append( 
            dict(url = export.short_uid,
                 path = export.filename,
                 name = export.experiment.name,
                 filesize = export.filesize,
                 datetime = export.datetime)
        )

    context = dict(title = 'Experiment data listing',
                   PLAY_EXPERIMENT_ROOT = PLAY_EXPERIMENT_ROOT,
                   export_list = export_list)

    return http_response(request, 'dataexport/listing.html', context)

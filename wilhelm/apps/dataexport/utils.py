from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import os
import json
import datetime
import tempfile
import tarfile

#=============================================================================
# Django imports
#=============================================================================
from django.conf import settings

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils import sys, strings

#=============================================================================
# Local imports 
#=============================================================================
from . import conf

#================================ End Imports ================================


def safe_export_data(export_dict, key, f):

    """
    For a given function `f` that will export data and place it in
    `export_dict` corresponding to key `key`, do this safely by catching any
    exception. Tell the calling function if the export was successful or not.

    """

    try:
        export_dict[key] = f()
        exception_raised = False
        exception_msg = None
    except Exception as e:
        exception_type = e.__class__.__name__
        exception_msg = 'Could not export %s. %s : %s' % (key,
                                                          exception_type,
                                                          e.message)

        export_dict[key] = None
        exception_raised = True

    return export_dict, exception_raised, exception_msg

def data_export_filter(obj):

    """ How to handle un-json-able data types.

    Wrap very long (>70) lines.

    """


    if type(obj) is datetime.datetime:

        return obj.strftime(conf.isoformat)

def tojson(export_dict):

    return json.dumps(export_dict,
                      default=data_export_filter,
                      indent=conf.indent_level)

def make_tarball(data_dir,
                 boilerplates,
                 label,
                 compression_method='bz2',
                 checksum_filename='checksum.txt'):

    '''
    Create bz2 (or gz) tarball of files in dirname directory. Run a checksum on
    file contents and append this information to the tarball.
    '''

    tarball_ext = '.tar.' + compression_method
    tarfile_method = 'w:' + compression_method

    tarball_filename = label + tarball_ext
    tarballs_directory = conf.data_archives_cache
    tarfile_path = os.path.join(tarballs_directory, tarball_filename)

    with tarfile.open(tarfile_path, tarfile_method) as tarball:
        
        checksums = []
        for (full_path, 
             relative_path, 
             checksum) in sys.list_directory_checksums(data_dir, 
                                                       algorithm=conf.default_hash_algorithm[0]):

            checksums.append((checksum, relative_path))
            tarball.add(full_path, arcname=relative_path)

        checksum_txt\
            = '\n'.join(['%s %s' % checksum for checksum in checksums])+'\n'

        boilerplates.append((checksum_filename, checksum_txt))

        for (boilerplate_filename, 
             boilerplate_file_content) in boilerplates:

            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            tmpfile.write(boilerplate_file_content)
            tmpfile.close()
            os.chmod(tmpfile.name, 0644)
            tarball.add(tmpfile.name, boilerplate_filename)
            os.unlink(tmpfile.name)

    tarball_filesize = human_readable(os.path.getsize(tarfile_path))

    return tarball_filename, checksums, tarball_filesize

def human_readable(filesize, suffix='B'):

    """
    Return human readable file size units.
    
    Sweet little function from
    http://stackoverflow.com/a/1094933/1009979

    """

    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(filesize) < 1024.0:
            return "%3.1f%s%s" % (filesize, unit, suffix)
        filesize /= 1024.0

    return "%.1f%s%s" % (filesize, 'Yi', suffix)

def make_release_label(experiment_name, datetime_now, uid):
    
    """
    Return label for experiment data export. 
    E.g., "foobar.140103032107.ab1c2ab".

    """
    
    return '_'.join(
        ['data',
         experiment_name,
         datetime_now.strftime(conf.data_export_timestamp_format),
         uid[:settings.UID_SHORT_LENGTH]]
    )

def make_readme(readme_template,
                experiment_name,
                experiment_url,
                uid,
                short_uid,
                datetime_now):

    introduction = readme_template['introduction']

    timestamp = readme_template['timestamp'].format(
        EXPORT_DATE = datetime_now.strftime(conf.human_readable_date_format),
        EXPORT_TIME = datetime_now.strftime(conf.human_readable_time_format)
        )

    unique_id = readme_template['unique_id'].format(UNIQUE_ID = short_uid)

    permalink = readme_template['permalink']

    checksum_info = readme_template['checksum_info']

    readme = "\n\n".join(
        [strings.wrapit(text) for text in (introduction, 
                                           timestamp, 
                                           unique_id,
                                           permalink,
                                           checksum_info)]
    )+'\n'

    return readme.format(
        PERMALINK= '\n' + settings.DATA_PERMALINK_ROOT + short_uid,
        EXPERIMENT_NAME = experiment_name,
        EXPERIMENT_URL = '\n'+settings.WWWURL + '/' + experiment_name
    )

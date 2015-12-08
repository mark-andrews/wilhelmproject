'''
Names and configuration settings used in the experimentarchives app.

Warning: If you wish to change anything here, you should do so only at the
start of an installation. Changing anything here after that could lead to
unexpected and unwelcome behaviour.
'''
from __future__ import absolute_import

#=============================================================================
# Django imports
#=============================================================================
from django.conf import settings

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils.collections import Bunch

#================================ End Imports ================================

# Inside an experiments repository, the main python module with the scripts for
# the experiments will have this name.
repository_experiments_modulename = 'experiments'
repository_experiments_filename\
        = '.'.join([repository_experiments_modulename, 'py'])

# The name of the configobj settings file inside an experiments repository.
repository_settings_filename = 'settings.cfg'

# The spec for the configobj settings file inside an experiments repository.
repository_settings_configspec = '''
    [experiments]
    [[__many__]]
    include = list(default=None)
    release-note = string(default='The latest version.')'''.strip().split('\n')

experiment_archives_cache = settings.EXPERIMENT_ARCHIVES_CACHE

# Default git branch.
default_git_branch = 'master'

git_log_format = '--pretty=format:%H,%at'

# Git hash lengths
git_hash_length = 40
git_abbrev_hash_length = 7

# How we compress experiment archive tarballs.
tarball_compression_method = 'bz2' # bz2 or gz

# Inside each experiment tarball, we keep checksum info for integrity checks.
tarball_checksum = 'checksum.txt' # Name of the file of checksum info.

# When naming experiment versions, we use their datetime stamp to name them.
experiment_version_timestamp_format = '%y%m%d%H%M%S'

# Since/Until format
since_until_fmt = '%Y-%m-%d %H:%M:%S'

data_export_conf = Bunch(dict(experiment = 'Experiment',
                              experiment_name = 'Experiment_name',
                              experiment_title = 'Title',
                              experiment_date_created = 'Date_created',
                              experiment_max_attempts = 'Max_attempts',
                              experiment_live = 'Live',
                              experiment_versions = 'Experiment_versions',
                              indent_level = 2,
                              widget_type = 'Widget',
                              slide_type = 'Slide',
                              playlist_type = 'Playlist',
                              slide_widgets = 'Widgets',
                              playlist_slides = 'Slides',
                              object_type = 'Type',
                              object_name = 'Name',
                              object_initialized = 'Initialized',
                              object_started = 'Started',
                              object_completed = 'Completed',
                              object_initialization_time = 'Initialization_datetime',
                              object_start_time = 'Start_datetime',
                              object_completed_time = 'Completed_datetime'))

from __future__ import absolute_import
from loremipsum import get_paragraph

#=============================================================================
# Standard library imports.
#=============================================================================
from random import choice
import configobj
import datetime
import distutils.dir_util
import glob
import os
import random
import sh
import shutil
import string
import tempfile

#=============================================================================
# Wilhelm imports
#=============================================================================
from . import conf, mock_subjects
from apps.archives import conf as archives_conf
from apps.subjects.utils import subject_enroll
from apps.archives import models as archives_models
from apps.core.utils import sys

#================================ End Imports ================================


this_dir = os.path.abspath(os.path.dirname(__file__))

def rndstring(string_length, chars = string.lowercase):

    """
    Create a random string of `chars` of len `string_length`.

    """

    return ''.join([choice(chars) for _ in xrange(string_length)])


def rndpasswd(password_length, chars = string.letters + string.digits):

    """
    Create a password of length `password_length` of (by default) randomly
    chosen alpha-numeric characters.

    """
    
    return rndstring(password_length, chars)


def rndemail(prefix_length = 10, suffix_length = 5):

    """
    Create a random email address: something@something.{org,com,net}

    """

    prefix = rndstring(prefix_length)
    suffix = rndstring(suffix_length)

    return prefix + '@' + suffix + '.' + choice(['org', 'com', 'net'])


def get_date_arg(date):
    ''' Provide a --date arg for git.
    Given a datetime object, format it according to the specified
    datetimeformat and return this in a command line argument for git.
    '''
    return ['--date="'+date.strftime(conf.datetimeformat)+'"']


def random_date_increment(date):
    '''
    Increment the date by a random number of days, hours, minutes and seconds.
    '''
    return date + datetime.timedelta(days = random.randint(1,5),
                                     hours = random.randint(0,24), 
                                     minutes = random.randint(0,60), 
                                     seconds = random.randint(0,60)
                                     )
def get_mock_users():
    test_users = []
    for email, details in mock_subjects.items():
        username = email
        password = details['password']
        test_users.append((username, password))

    return test_users

def enroll_mock_subjects():
    return subject_enroll(mock_subjects)

class GenericSetup(object):
    '''
    This is a general setup for tests. 
    Primarily, it involves the creation of a mock ExperimentRepository and its
    accompanying Experiment and ExperimentVersion models.

    '''

    def __init__(self):

        # Make some mock subjects.

        # Make a mock git project.
        self.mock_repository_setup_dir = make_mock_repository_files()

        self.mock_repository = MockExperimentRepository(
                setup_dir = self.mock_repository_setup_dir)

        self.mock_repository.initialize()

        self.number_of_revisions = 10

        self.mock_repository.update(revisions=self.number_of_revisions)

        # Make a repository, archives, etc for the experiments.
        setup_fields = dict(name = 'mock',
                            description = 'A mock repository',
                            date_created = datetime.datetime.now(),
                            is_active = True,
                            path = self.mock_repository.path)

        self.experiment_repository\
            = archives_models.ExperimentRepository.objects.create(
                **setup_fields)

        self.experiment_repository.make_archives()

        # Set current version to default.
        archives_models.Experiment.objects.set_default_current_version()

    def __del__(self):
        '''
        Cleaning up the artifacts created by this generic setup.
        '''
        shutil.rmtree(self.mock_repository.path)
        shutil.rmtree(self.mock_repository_setup_dir)


def read_mock_file(mock_file_name):

    '''
    Read in the given mock file, assuming it is in
    this_dir/`conf.mock_repository_setup_dir`.
    '''

    return open(os.path.join(this_dir, 
                                conf.mock_repository_setup_dir,
                                mock_file_name)
                ).read()

def make_mock_repository_files():
    '''
    Make the files for the mock repository from the templates.
    '''


    experiments_header, experiment_template, stimuli_text\
        = map(read_mock_file, (conf.mock_repository_header,
                               conf.mock_repository_experiment_template,
                               conf.mock_stimuli_template))


# TODO: Obsolete (I think). August 20, 2014.
#
#    experiments_header = open(os.path.join(this_dir,
#                                           conf.mock_repository_setup_dir,
#                                           conf.mock_repository_header)
#                              ).read()
#
#    experiment_template\
#        = open(os.path.join(this_dir,
#                            conf.mock_repository_setup_dir,
#                            conf.mock_repository_experiment_template)
#               ).read()
#
#    stimuli_text = open(os.path.join(this_dir,
#                                         conf.mock_repository_setup_dir,
#                                         conf.mock_stimuli_template)
#                               ).read()
#

    cfg_template = conf.mock_repository_cfg_template

    experiments_py_list = [experiments_header]
    cfg_file_list = ['[experiments]']
    stimuli_files = {}
    for experiment_name in conf.mock_experiment_names:
        class_name = experiment_name
        name = experiment_name.lower()
        experiments_py_list.append(experiment_template.format(class_name,
                                                              name)
                                   )
        cfg_file_list.append(cfg_template.format(class_name, name))
        stimuli_files[name + '.cfg']\
            = conf.mock_stimuli_randomtext + '\n' + stimuli_text

    experiments_py = '\n\n'.join(experiments_py_list)
    cfg_file = '\n'.join(cfg_file_list)

    tmpdir = tempfile.mkdtemp()

    # Write the experiments.py file.
    with open(os.path.join(tmpdir, conf.experiments_py_name), 'w') as f:
        f.write(experiments_py)

    # Write the settings.cfg file.
    with open(os.path.join(tmpdir, conf.settings_cfg_name), 'w') as f:
        f.write(cfg_file)


    # Create the stimuli dir.
    os.mkdir(os.path.join(tmpdir, conf.stimuli_dir_name))
    
    # For each stimulus cfg file, copy it into a file in stimuli dir.
    for filename, cfg_contents in stimuli_files.items():
        with open(os.path.join(tmpdir,
                               conf.stimuli_dir_name,
                               filename), 'w') as f:
            f.write(cfg_contents)

    return tmpdir # Return name.

# FIXME. This is obsolete now (May 25, 2014).
#def make_mock_archive():
#    '''
#    Using the information in conf.mock_archive, make a tarball and get the
#    experiment
#    Make a tarball of the experimets archive.
#    Also return all the experiment details.
#    '''
#
#    # Create a short-cut to this object.
#    compression_method = archives_conf.tarball_compression_method
#
#    # Make a temporary directory for the tarball. Get the name of the tarball
#    # file.
#    tmpdir = tempfile.mkdtemp()
#    tarball_filename = conf.mock_archive + '.' + compression_method
#    tarfile_path = os.path.join(tmpdir, tarball_filename)
#
#    # Full path name of the mock archive.
#    mock_archive = os.path.join(this_dir, conf.mock_archive)
#
#    # Put all the files in the mock archive into the tarball.
#    # Also, do a sha1sum of each file for the pursposes of an integrity check.
#    with tarfile.open(tarfile_path, 'w:'+compression_method) as tarball:
#
#        file_hash_list = []
#        for full_path, relative_path, checksum\
#                in sys.list_directory_checksums(mock_archive):
#            file_hash_list.append('%s %s' % (relative_path, checksum))
#            tarball.add(full_path, arcname=relative_path)
#
#        tmpfile = tempfile.NamedTemporaryFile(delete=False)
#        tmpfile.write('\n'.join(file_hash_list)+'\n')
#        tmpfile.close()
#        os.chmod(tmpfile.name, 0644)
#        tarball.add(tmpfile.name, archives_conf.tarball_checksum)
#        os.unlink(tmpfile.name)
#
#    # Make a temporary directory.
#    mock_archive_tmpdir = tempfile.mkdtemp()
#
#    # Copy the contents of the mock archive into the temporary directory.
#    distutils.dir_util.copy_tree(mock_archive, mock_archive_tmpdir)
#
#    # Get all the details of the experiments in the archive.
#    experiment_details\
#        = archives_utils.get_experiment_details(mock_archive_tmpdir)
#    
#    # Zap the temporary directory.
#    shutil.rmtree(mock_archive_tmpdir)
#
#
#    return tarfile_path, experiment_details

class MockExperimentRepository(object):
    '''
    A mock repository to test the make_archives ExperimentRepository model.
    This uses the mock_repository_setup/ files.
    '''

    def __init__(self, setup_dir, initial_date=None):
        if initial_date is None:
            initial_date = datetime.datetime.now()
        self.path = tempfile.mkdtemp()
        self.git = sh.git.bake('--no-pager', _cwd=self.path)

        self.initial_date = initial_date
        self.commits = []

        # Read in the names of the stimuli files.   
        self.test_setup_dir = setup_dir
        distutils.dir_util.copy_tree(self.test_setup_dir, self.path)

        self.mock_filenames\
                = glob.glob(os.path.join(self.path, 'stimuli', '*.cfg'))

        self.commit_dictionary = {}


    def write_mockfiles(self, append=True):

        for filename in self.mock_filenames:
            paragraph = get_paragraph()
            C = configobj.ConfigObj(filename)
            text = C['randomtext']['text'].strip()
            if append:
                text += paragraph
            else:
                text = paragraph
            C['randomtext']['text'] = text
            C.write()
            self.git(['add', filename])

    def initialize(self):

        self.git(['init'])
        self.git(['add', 'experiments.py', 'settings.cfg', 'stimuli/'])
        self.write_mockfiles(append=False)
        self.commit(self.initial_date, msg='Initial commit')

    def update(self, revisions=10, date=None):

        if not date:
            date = self.initial_date

        for revision in xrange(revisions):
            date = random_date_increment(date)
            self.write_mockfiles()
            self.commit(date, msg='Made random revision %d.' % revision)

    def commit(self, date, msg='A commit'):
        ''' Issue a git commit.
        Record the tree structure snapshot, return the commit details.
        '''
        git_args = ['commit', '-m', msg]
        git_args += get_date_arg(date)
        self.git(git_args)
        
        arguments = ['log', '-n', '1']
        arguments.append(archives_conf.git_log_format)

        _hash, tstamp\
                = self.git(*arguments).stdout.strip().split(',')

        self.commit_dictionary[_hash]\
                = sys.list_directory_checksums(self.path)

    def get_all_commits(self):
        arguments = ['log']
        arguments.append(archives_conf.git_log_format)

        commits = []
        for commit_info in self.git(*arguments).stdout.strip().split('\n'):

            commit_hash, commit_datetime = commit_info.split(',')

            commit_datetime\
            = datetime.datetime.fromtimestamp(int(commit_datetime))

            commits.append((commit_hash, commit_datetime))

        return commits

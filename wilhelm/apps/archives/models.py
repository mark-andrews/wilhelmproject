'''
Models for the experimental archives.
'''

from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
from collections import OrderedDict
import os
import sh
import logging

#=============================================================================
# Third party imports.
#=============================================================================
import configobj, validate

#=============================================================================
# Django imports.
#=============================================================================
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

#=============================================================================
# Wilhelm imports
#=============================================================================
from . import conf, utils
from .conf import data_export_conf
from apps.core.utils import git, python, datetime, strings
from apps.dataexport.utils import safe_export_data

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')

class ExperimentRepository(models.Model):

    '''
    A wilhelm experiment repository.
    Its primary attribute is the path to a git repository.
    We'll also give it a name, a description and state whether it is active.

    Its primary method is `make_archives`, which archives all versions of the
    repository and updates the ExperimentArchives, ExperimentVersions and
    Experiments models.
    '''

    name = models.CharField(max_length=settings.NAME_LENGTH,
                            null=True)
    path = models.CharField(max_length=128, null=True)
    remote_server = models.CharField(max_length=256, null=True)

    date_created = models.DateTimeField(null=True)

    branch = models.CharField(default=conf.default_git_branch, 
                              max_length=250,
                              null=True)
    description = models.TextField(null=True)
    is_active = models.BooleanField(default=True)

    @classmethod
    def new(cls, path_to_git_repository):

        name = os.path.basename(path_to_git_repository)

        try:
            repository = cls.objects.get(name = name, 
                                         path = path_to_git_repository)

        except ObjectDoesNotExist:

            repository = cls.objects.create(name = name,
                                            path = path_to_git_repository,
                                            date_created = datetime.now())

        return repository



    #=========================================================================
    # Public methods.
    #=========================================================================
    def make_archives(self):
        ''' 
        This is unsafe for general use, but is handy for use with tests.
        Create archives of all the versions in the repository whose dates
        lie between the `since` and `until` dates (including those to be
        explicitly included and excluding those to be explicitly excluded).

        As the archives are being made, trigger the ExperimentArchive to make
        all experiment in the archive.         
        '''

        for commit_hash, commit_datetime in self.get_all_commits():

            ExperimentArchive.new(repository=self,
                                  commit_hash = commit_hash)



    def get_all_commits(self):
        ''' Return a list of all commits on the branch of the git project.

        Return as list of tuples: (hash, timestamp). Sort by date.
        '''

        git_cmd = sh.git.bake('--no-pager', _cwd=self.path)

        arguments = ['log']
        arguments.append(conf.git_log_format)
        arguments.append(self.branch)

        commits = []
        for commit_info in git_cmd(*arguments).stdout.strip().split('\n'):

            commit_hash, commit_datetime = commit_info.split(',')

            commit_datetime = git.fromtimestamp(commit_datetime)

            commits.append(
                (commit_hash, commit_datetime)
            )

        return sorted(commits, 
                      key = lambda element : element[1],
                      reverse = True)

    def get_head_commit(self):

        all_commits = self.get_all_commits()
        return all_commits[0]

    def get_all_commits_as_dict(self):

        return {commit_hash: (commit_hash, commit_date)
                for commit_hash, commit_date in self.get_all_commits()
                }

    def has_commit(self, commit_hash):

        try:
            self.get_commit(commit_hash)
            return True
        except KeyError:
            return False

    def get_commit(self, commit_hash):
        
        '''
        A bit of brute force-ish way to get what 

        git show -s --format=%H,%at commit_hash 

        would give.

        It raise a KeyError is there is no such commit_hash in the repo.

        The commit_hash may be an abbreviated version of the full hash, so long
        as that abbreviated version is unique.

        '''

        commits = self.get_all_commits_as_dict()
        K = len(commit_hash)

        if K > conf.git_hash_length:
            raise KeyError

        if K == conf.git_hash_length:
            return commits[commit_hash]

        else:

            matches = [key[:K] == commit_hash for key in commits.keys()]
            if sum(matches) == 0:
                raise KeyError
            elif sum(matches) == 1:
                commit_hash = [key for key in commits.keys() if key[:K] == commit_hash].pop()
            else:
                raise Exception('More than one hash matches %s' % commit_hash)

            return commits[commit_hash]




class ExperimentArchive(models.Model):

    '''
    Releases of ExperimentRepository.
    '''

    repository = models.ForeignKey(ExperimentRepository)
    commit_hash = models.CharField(max_length=40, unique=True)
    commit_date = models.DateTimeField(null=True, blank=True)

    #=========================================================================
    # Class methods.
    #=========================================================================
    @classmethod
    def new(cls, repository, commit_hash):

        commit_hash, commit_date = repository.get_commit(commit_hash)

        try:
            experiment_archive = cls.objects.get(repository = repository,
                                                 commit_hash = commit_hash)

        except ObjectDoesNotExist:


            experiment_archive = cls.objects.create(repository = repository,
                                                    commit_hash = commit_hash,
                                                    commit_date = commit_date)

        experiment_archive.make_experiments()

        return experiment_archive

    #=========================================================================
    # Instance method.
    #=========================================================================
    def make_experiments(self):

        '''
        Create experiment versions (and their experiment parents, if necessary)
        for each experiment listed in this archive. The creation entails the
        creation of playlists for each experiment.
        '''

        exported_archive = git.export(self.repository.path,
                                      self.commit_hash)

        experiments_module = python.impfromsource(
            conf.repository_experiments_modulename, exported_archive
        )

        experiments_settings = os.path.join(exported_archive,
                                            conf.repository_settings_filename)

        config = configobj.ConfigObj(
            experiments_settings,
            configspec = conf.repository_settings_configspec
            )

        validator = validate.Validator()

        assert config.validate(validator, copy=True)

        for class_name, experiment_notes in config['experiments'].items():

            label = utils.make_experiment_release_code(class_name,
                                                       self)

            release_note = experiment_notes['release-note']

            try:

                playlist_factory = getattr(experiments_module, class_name)

            except AttributeError:

                error_msg = strings.msg('''
                No experiment named %s in the repository %s (commit hash: %s).
                ''' % (class_name, self.repository.name, self.commit_hash)
                )

                print(error_msg) # You could log it too.

                raise

            playlist = playlist_factory.new()

            ExperimentVersion.new(
                experiment=Experiment.new(class_name=class_name),
                label=label,
                release_note=release_note,
                playlist=playlist,
                archive=self)


    #=========================================================================
    # Properties.
    #=========================================================================
    @property
    def commit_abbreviated_hash(self):
        '''
        Return the first 7 (it's always 7, right?) characters of the commit hash.
        '''
        return self.commit_hash[:7]


class ExperimentVersion(models.Model):

    '''
    An ExperimentVersion specifies a python class name, the experiment archive
    where that class and any accompanying files can be found, a dictionary of
    the names and checksums of the relevant files and python code in the
    archive, and a release note about that experiment.

    This information is used for accounting purposes. The code and data for the
    experiment itself are imported from an ExperimentArchive object.
    '''

    experiment = models.ForeignKey('Experiment', 
                                   related_name='experiment',
                                   null=True
                                   )
    
    label = models.CharField(max_length=50, unique=True, primary_key=True)
    release_note = models.TextField()

    playlist_ct = models.ForeignKey(ContentType,
                                    related_name = '%(app_label)s_%(class)s_as_playlist',
                                    null=True)

    playlist_uid = models.CharField(max_length=settings.UID_LENGTH, null=True)
    playlist_fk = GenericForeignKey('playlist_ct', 'playlist_uid')

    archive = models.ForeignKey(ExperimentArchive)

    #=========================================================================
    # Class methods.
    #=========================================================================
    @classmethod
    def new(cls,
            experiment,
            label,
            release_note,
            playlist,
            archive):


        experiment_version, _created = cls.objects.get_or_create(
            experiment=experiment,
            label=label,
            release_note=release_note,
            playlist_uid=playlist.uid,
            playlist_ct=ContentType.objects.get_for_model(playlist),
            archive=archive
        )

        experiment.set_default_current_version()

        return experiment_version

    #=========================================================================
    # Properties..
    #=========================================================================
    @property
    def playlist(self):
        playlist = self.playlist_ct.model_class()
        return playlist.objects.get(uid = self.playlist_uid)

    @playlist.setter
    def playlist(self, playlist):

        _ct = ContentType.objects.get_for_model(playlist)
        _uid = playlist.uid

        setattr(self, 'playlist_ct', _ct)
        setattr(self, 'playlist_uid', _uid)

        self.save()

    @property
    def name(self):
        '''
        Return the name of the experiment of which this is a version.
        '''
        return self.experiment.name

    def data_export(self):

        """
        Export all of the general information related to this experiment
        version. 
        """

        export_dict = OrderedDict()

        for key, f in [
            ('Label', lambda: self.label),
            ('Release note', lambda: self.release_note),
            ('Playlist uid', lambda: self.playlist.uid),
            ('Repository', lambda: self.archive.repository.name),
            ('Repository path', lambda: self.archive.repository.path),
            ('Repository remote', lambda: self.archive.repository.remote_server),
            ('Commit hash', lambda: self.archive.commit_hash),
            ('Commit date', lambda: self.archive.commit_date)]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict


class ExperimentManager(models.Manager):

    def set_default_current_version(self):
        ''' For all experiment that do not yet have an experiment version as
        their current version, set the current version as the most recent
        experiment version.'''
        no_current_version_yet_experiments = self.filter(current_version =
                                                         None)
        for experiment in no_current_version_yet_experiments:
            most_recent_experiment_version\
                = ExperimentVersion.objects.\
                filter(experiment=experiment).latest('archive__commit_date')
            experiment.current_version = most_recent_experiment_version
            experiment.save()

        return no_current_version_yet_experiments # Useful for testing.

    def get_name_regex(self):
        return  r'|'.join([exp.name for exp in self.all()])

class Experiment(models.Model):

    '''
    An "Experiment" as defined here is a container of ExperimentVersions, which
    are pointers to the experiment tar balls.
    '''

    #=========================================================================
    # Model fields
    #=========================================================================
    class_name = models.CharField(max_length=50, primary_key=True)
    date_created = models.DateTimeField(null=True, blank=True)

    # Which version of the experiment is currently running.
    current_version = models.ForeignKey('ExperimentVersion',
                                        null=True,
                                        related_name='currentversion')

    # This will be used for adverstising.
    blurb = models.TextField(null=True)
    title = models.CharField(null=True, max_length=100)

    # Is it live?
    live = models.BooleanField(default=False)

    # Max number of attempts by each subject. If null, then unlimited.
    attempts = models.IntegerField(null=True, default=1)

    #=========================================================================
    # Model manager
    #=========================================================================
    objects = ExperimentManager()


    #=========================================================================
    # Class methods
    #=========================================================================
    @classmethod
    def new(cls, class_name):

        try:

            experiment = cls.objects.get(class_name=class_name)

        except ObjectDoesNotExist:

            experiment = cls.objects.create(class_name=class_name,
                                            date_created=datetime.now())

        return experiment

    #=========================================================================
    # Instance methods
    #=========================================================================
    def set_default_current_version(self):

        '''
        If there is no current version set, then set the current version.
        '''

        #if not self.current_version:

        most_recent_experiment_version\
            = ExperimentVersion.objects\
            .filter(experiment=self).latest('archive__commit_date')

        self.current_version = most_recent_experiment_version
        self.save()

    def data_export(self):

        export_dict = OrderedDict()

        for key, f in [
            (data_export_conf.experiment, lambda: self.class_name),
            (data_export_conf.experiment_name, lambda: self.name),
            (data_export_conf.experiment_title, lambda: self.title),
            (data_export_conf.experiment_date_created, lambda: self.date_created),
            (data_export_conf.experiment_max_attempts, lambda: self.attempts),
            (data_export_conf.experiment_live, lambda: self.live),
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def get_all_versions(self):

        """ Return all versions of this experiment.

        """

        return ExperimentVersion.objects.filter(experiment=self)

    #=========================================================================
    # Properties
    #=========================================================================
    @property
    def name(self):
        return self.class_name.lower()

    @property
    def single_attempt_only(self):

        '''
        If attempts == 1, then only one attempt at this experiment is allowed.
        If attempts > 1, then more than one attempt is allowed.
        If attempts == None, then an unlimited number of attempts are allowed.
        '''

        if self.attempts == 1:
            return True
        else:
            return False


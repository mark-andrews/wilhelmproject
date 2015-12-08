from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import sh
import tempfile
import os
import shutil
import inspect
import tarfile

#=============================================================================
# Wilhelm imports
#=============================================================================
from apps.core.utils import sys, python
from . import conf

#=============================================================================
# Third party imports.
#=============================================================================
import configobj, validate

#================================ End Imports ================================

def make_tarball(project, _hash):
    '''
    Create tar.bz2 (or .gz) ball for the experiments directory at a given
    commit.
    '''

    tarball_ext = '.tar.' + conf.tarball_compression_method
    tarfile_method = 'w:' + conf.tarball_compression_method

    tarfile_name = _hash + tarball_ext
    tarballs_directory = conf.experiment_archives_cache
    tarfile_path = os.path.join(tarballs_directory, tarfile_name)

    with tarfile.open(tarfile_path, tarfile_method) as tarball:
        
        export_tmpdir = git_export(project, _hash)

        file_hash_list = []
        for full_path, relative_path, checksum\
        in sys.list_directory_checksums(export_tmpdir):
            file_hash_list.append('%s %s' % (relative_path, checksum))
            tarball.add(full_path, arcname=relative_path)

        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmpfile.write('\n'.join(file_hash_list)+'\n')
        tmpfile.close()
        os.chmod(tmpfile.name, 0644)
        tarball.add(tmpfile.name, conf.tarball_checksum)
        os.unlink(tmpfile.name)

    experiment_details = get_experiment_details(export_tmpdir)
    shutil.rmtree(export_tmpdir) # Zap export dir.

    return experiment_details, tarfile_path

def git_export(project, _hash):
    '''
    Export commit `_hash` of git project `project` into a temporary directory.
    Return the name of the temporary directory.
    The process requires tar-ing and untar-ing.
    '''
    tmpdir = tempfile.mkdtemp()
    tarball_name = os.path.join(tmpdir, 'exported_git_project.tar')
    assert os.path.exists(project) and os.path.isdir(project)
    git = sh.git.bake(_cwd=project)
    git('archive', _hash, '-o', tarball_name)
    export_tmpdir = tempfile.mkdtemp()
    sh.tar('-xf', tarball_name, '-C', export_tmpdir)
    shutil.rmtree(tmpdir) # Delete the tmpdir.

    return export_tmpdir 

def get_experiment_details(exported_archive):
    '''
    Using the settings.cfg file inside the exported wilhelm
    experiments_directory, get the checksum of the source code of the
    Playlist sub class for each experiment listed therein as well as the
    file path names and checksums of the included files.

    This information is useful only to check if the relevant source and stimuli
    files for a given experiment change from one repository version to another.
    If they have changed, we know the experiment has changed.

    Return as dictionary of lists of tuples.
    '''

    experiments_module = python.impfromsource(
        conf.repository_experiments_modulename, exported_archive
    )

    experiments_settings\
    = os.path.join(exported_archive, conf.repository_settings_filename)

    config = configobj.ConfigObj(
        experiments_settings,
        configspec = conf.repository_settings_configspec
        )

    validator = validate.Validator()
    assert config.validate(validator, copy=True)

    experiments_dir = {}
    for class_name, expdict in config['experiments'].items():

        release_note = expdict['release-note']

        experiment_source = inspect.getsource(
            getattr(experiments_module, class_name)
            )

        file_info = dict(
            class_source = sys.checksum(experiment_source)
            )
       
        for filename in expdict['include']:

            file_hash = sys.checksum(
                os.path.join(exported_archive, filename)
            )

            file_info[filename] = file_hash

        experiments_dir[class_name] = dict(
                release_note = release_note, 
                file_info = file_info)

    return experiments_dir

# TODO (Fri 22 Aug 2014 02:18:07 BST): Obsolete.
def list_all_experiments(exported_archive):

    experiments_module = python.impfromsource(
        conf.repository_experiments_modulename, exported_archive
    )

    experiments_settings\
    = os.path.join(exported_archive, conf.repository_settings_filename)

    config = configobj.ConfigObj(
        experiments_settings,
        configspec = conf.repository_settings_configspec
        )

    validator = validate.Validator()
    assert config.validate(validator, copy=True)

    experiments = []
    for class_name in config['experiments']:

        try:

            getattr(experiments_module, class_name)

        except AttributeError:

            raise AssertionError('No such experiment: %s' % class_name)

        
        experiments.append(class_name)

    return experiments



def make_experiment_release_code(class_name, experiment_archive):
    '''Create the unique label.
    The class name (but in lowercase), followed by a date-time
    stamp (like 131120135113 for 13, 11, 20, 13, 51, 13),
    followed by a 7 hex char hash abbreviation of the archive. These three
    fields are delimited by '_'.
    For example, foo_1311201351130_bd06e3
    '''

    return '_'.join([class_name.lower(), 
                     experiment_archive.commit_date.strftime(
                        conf.experiment_version_timestamp_format
                     ), 
                     experiment_archive.commit_abbreviated_hash
                     ])


def import_experiment(tarball_path):
    '''
    Import and return the `experiments` module located in the tarball at
    `tarball_path`.
    '''

    tarball_model = ExperimentArchiveTarball(tarball_path)

    return tarball_model.import_experiments()


class ExperimentArchiveTarball(object):
    '''
    A class for representing and acting on the information in the exported
    tarball archive of wilhelm experiments.

    The primary function is to check the contents of the tarball to see if it
    is working.
    '''
    def __init__(self, tarball_path):


        compression_method = conf.tarball_compression_method
        self.tarfile_method = 'r:' + compression_method

        ###############
        # Some checks #
        ###############

        compression_method_info\
        = {'bz2': ('bzip2', '.bz2'), 'gz': ('gzip', '.gz')}

        # Are we dealing with a compressed tar file?
        sys.assert_file_exists(tarball_path)
        assert tarfile.is_tarfile(tarball_path),\
                '%s is not a tarball.' % tarball_path

        compression_type, compression_ext\
                = compression_method_info[compression_method]

        assert compression_type in sh.file(tarball_path),\
                '%s is not %s?' % (tarball_path, compression_method)

        root, ext = os.path.splitext(tarball_path)
        assert ext == compression_ext,\
                '%s is not %s?' % (tarball_path, compression_method)

        #################
        # Checks passed #
        #################

        self.tarball_path = tarball_path

        # Get the name of the directory where we will extract the tarball, and
        # then zap any file or dir by that name and create an empty directory.
        root, ext = os.path.splitext(self.tarball_path) # knock of the .bz2
        root, ext = os.path.splitext(root) # knock of the .tar
        self.extraction_dir = os.path.basename(root)

    def extract(self):
        '''Extract the tarball into the moduledirectory.
        We will clear the contents of the extraction_directory first.
        '''

        self._make_extraction_dir()

        tarballobj = tarfile.open(self.tarball_path, self.tarfile_method)
        tarballobj.extractall(path = self.extraction_dir)

        assert self._extracted_archive_check()

    def integrity_check(self):
        '''
        Create and delete the extracted archive. If it works, then the
        _extracted_archive_check will have passed.
        '''

        self.extract()
        shutil.rmtree(self.extraction_dir)

        return True # If you get this far, that is good.

    def import_experiments(self):
        '''
        Import the experiments from wilhelm_experiments tarball.
        '''

        self.extract()

        # Import the experiments.
        experiments = python.impfromsource(
            conf.repository_experiments_modulename, self.extraction_dir
        )

        shutil.rmtree(self.extraction_dir)

        return experiments

    def import_check(self):
        '''
        Check that the experiment in the tarball imports properly.
        '''
        # Does this import raise any exceptions?
        self.import_experiments()
        return True # If you get this far, that is good.

    def _make_extraction_dir(self):
        '''
        Check if the extraction_dir exists. If so, zap it and make it again.
        '''

        if os.path.exists(self.extraction_dir):
            if os.path.isdir(self.extraction_dir):
                shutil.rmtree(self.extraction_dir)
            elif os.path.isfile(self.extraction_dir):
                os.unlink(self.extraction_dir)

        sys.mkdir_p(self.extraction_dir)

    def _extracted_archive_check(self):
        ''' Does extraction_dir contain the extracted contents of the archive
        tarball?  '''

        with tarfile.open(self.tarball_path, self.tarfile_method) as tarball:
            checksum_string\
                    = tarball.extractfile(conf.tarball_checksum).read().strip()

        for line in checksum_string.split('\n'):
            relative_filepath, hashsum = line.split()
            fullpath = os.path.join(self.extraction_dir, relative_filepath)
            sys.assert_file_exists(fullpath)
            assert sys.checksum(fullpath) == hashsum

        return True # If we get this far.

def parse_repository(repository):

    '''
    Given cfg file with contents e.g. 

    [repository]
        ['circus']
            path = '/path/to/dir/'
            since = '%Y-%m-%d %H:%M:%S'
            until = '%Y-%m-%d %H:%M:%S'
            exclude = abcde....xyz, ABCDE...XYZ
            include = abcde....xyz, ABCDE...XYZ

    parse it and return the path and since and until as datatime objects. Check
    if the path exists and is dir.

    To be used as part of a management command.

    '''

    try:
        path = os.path.abspath(repository['path'])
        assert os.path.exists(path) and os.path.isdir(path)

    except KeyError:
        path = None

    except AssertionError:
        sys.stderr.write('Does "%s" exist and is it a directory?' % path)
        raise


    since_until = dict(since=None, until=None)

    for since_or_until in since_until:

        try:

            since_until[since_or_until]\
                = datetime.datetime.strptime(repository[since_or_until],
                                             conf.since_until_fmt)

        except KeyError:
            pass

        except ValueError:
            sys.stderr.write('Datetime "%s" should be formatted as "%".'
                             % (repository[since_or_until], 
                                conf.since_until_fmt)
                             )

            raise

    include_exclude = dict(include=[], exclude=[])

    for include_or_exclude in include_exclude:

        try:
            include_exclude[include_or_exclude]\
                = repository[include_or_exclude]
        except KeyError:
            pass

    return (path,
            since_until['since'], 
            since_until['until'], 
            include_exclude['include'],
            include_exclude['exclude'])

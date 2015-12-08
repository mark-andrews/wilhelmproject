from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import sh
import tempfile
import os
import shutil
import tarfile
import datetime

#=============================================================================
# Wilhelm imports
#=============================================================================
from . import sys

#================================ End Imports ================================

def export(project, commit_hash):

    ''' 
    Export commit `commit_hash` of git project `project` into a temporary
    directory.  Return the name of the temporary directory.  The process
    requires tar-ing and untar-ing.  
    '''

    tmpdir = tempfile.mkdtemp()
    tarball_name = os.path.join(tmpdir, 'exported_git_project.tar')
    assert os.path.exists(project) and os.path.isdir(project)
    git = sh.git.bake(_cwd=project)
    git('archive', commit_hash, '-o', tarball_name)
    export_tmpdir = tempfile.mkdtemp()
    sh.tar('-xf', tarball_name, '-C', export_tmpdir)
    shutil.rmtree(tmpdir) # Delete the tmpdir.

    return export_tmpdir 

def make_tarball(project, 
                 commit_hash, 
                 tarball_compression_method='bz2',
                 export_directory='/tmp',
                 checksum='checksum.txt'):

    '''
    Create tar.bz2 (or .gz) tarball of the exported version of the git
    repository. 
    Put a checksum.txt inside the tarball too. A nice touch.
    Return the path to the tarball.
    '''

    tarball_ext = '.tar.' + tarball_compression_method
    tarfile_method = 'w:' + tarball_compression_method

    tarfile_name = commit_hash + tarball_ext
    tarfile_path = os.path.join(export_directory, tarfile_name)

    with tarfile.open(tarfile_path, tarfile_method) as tarball:
        
        export_tmpdir = export(project, commit_hash)

        file_hash_list = []
        for full_path, relative_path, checksum\
        in sys.list_directory_checksums(export_tmpdir):
            file_hash_list.append('%s %s' % (relative_path, checksum))
            tarball.add(full_path, arcname=relative_path)

        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        tmpfile.write('\n'.join(file_hash_list)+'\n')
        tmpfile.close()
        os.chmod(tmpfile.name, 0644)
        tarball.add(tmpfile.name, checksum)
        os.unlink(tmpfile.name)

    shutil.rmtree(export_tmpdir) # Zap export dir.

    return tarfile_path

def fromtimestamp(commit_timestamp):

    '''
    Given a commit timestamp (format %at), convert to a datetime.
    '''

    return datetime.datetime.fromtimestamp(int(commit_timestamp))

def get_all_commits(project, branch):
    # TODO (Thu 20 Aug 2015 03:43:45 BST): This will break.
    # There is no self, no conf.
    git_cmd = sh.git.bake('--no-pager', _cwd=self.path)

    arguments = ['log']
    # TODO (Mon Dec 15 19:28:56 2014): We got to be careful here. Putting
    # the git_log_format in a conf file implies that it is an arbitrary
    # parameter. However, it is not and if it is changed then the parsing
    # of the git_cmd will break. 
    arguments.append(conf.git_log_format)
    arguments.append(self.branch)

    commits = []
    for commit_info in git_cmd(*arguments).stdout.strip().split('\n'):

        commit_hash, commit_datetime\
            = commit_info.split(',')

        commit_datetime\
            = git.fromtimestamp(commit_datetime)

        commits.append(
            (commit_hash, commit_datetime)
        )

    return commits



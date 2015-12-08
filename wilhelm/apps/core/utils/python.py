
'''
Utilities to extend core python functionality.
'''
from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import inspect
import os
import imp

#================================ End Imports ================================
   
def isdescendant(the_child, the_ancestor):
    '''
    Is `the_child' object a descendant of `the_ancestor' object.
    '''
    
    for an_ancestor in inspect.getmro(the_child)[1:]: # Family lineage.
        if an_ancestor.__name__ == the_ancestor.__name__:
            return True

    return False # return False if we don't break out and return True

def impfromsource(filename, dirname):
    '''
    Import a module from source. 
    If the filename of the module does not end in '.py', add that to it.

    '''
    
    root, ext = os.path.splitext(filename)

    if ext != '.py':
        filename_ext = filename + '.py'
    else:
        filename_ext = filename


    fullpath = os.path.abspath(os.path.join(dirname, filename_ext))

    assert os.path.exists(fullpath), fullpath

    return imp.load_source(filename, fullpath)

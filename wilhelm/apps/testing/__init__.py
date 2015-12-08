import os
import configobj
this_dir = os.path.abspath(os.path.dirname(__file__))

mock_subjects\
    = configobj.ConfigObj(os.path.join(this_dir, 'mock_subjects.cfg'))

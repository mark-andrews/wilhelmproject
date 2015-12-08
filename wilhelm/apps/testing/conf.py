
datetimeformat = '%Y-%m-%d %H:%M:%S' # The string format used for datetimes.

mock_repository_setup_dir = 'mock_repository_setup'
mock_repository_header = 'experiments_header.txt'
mock_repository_experiment_template = 'experiment_template.txt'
mock_repository_cfg_template = '''
        [[{0}]]
            include = stimuli/{1}.cfg,
            release-note = 'This is a release of experiment {0}.'
    '''

mock_archive = 'mock_archive'
mock_stimuli_template = 'stimuli_template.txt'
mock_stimuli_randomtext\
= ''' [randomtext]
            text =	\'\'\' Lorem ipsum. \'\'\' '''

experiments_py_name = 'experiments.py'
settings_cfg_name = 'settings.cfg'
stimuli_dir_name = 'stimuli'



mock_experiment_names = 'Yarks Rusty Moers Fribs Leuco'.split()

import collections

live_experiment = 'live_experiment'
slide_to_be_launched = 'slide_to_be_launched'

live_session_elsewhere_error = 'live_session_elsewhere'
another_experiment_error = 'another_experiment_in_browser'
session_nowplaying_error = 'nowplaying'
attempts_completed_error = 'attempts_complete'

on_login_redirect_to = 'on_login_redirect_to'

Button = collections.namedtuple('Button', 
                                ('stop', 'pause', 'next', 'feedback'))
button = Button('Finish', 
                'Continue later', 
                'Continue now', 
                'Experiment feedback')

# TODO (Tue 09 Sep 2014 11:25:26 BST): Make into a dict.
Blockage = collections.namedtuple('Blockage', ('live_elsewhere',
                                               'wrong_experiment',
                                               'nowplaying',
                                               'attempts_complete')
                                  )
blockage = Blockage(
    'There is a live session in another browser session.',
    'A different experiment is already live in the browser session.',
    'A slide is nowplaying in the browser session.',
    'You have completed the total number of attempts for this experiment.'
)

# TODO (Tue 09 Sep 2014 11:25:09 BST): I think this is obsolete now.
SlideView = collections.namedtuple('SlideView', 
                                   ('InitialPlaylistSlideView',
                                    'LivePlaylistSlideView', 
                                    'PausedPlaylistSlideView',
                                    'RepeatPlaylistSlideView')
                                   )

slideview = SlideView(
    'InitialPlaylistSlideView',
    'LivePlaylistSlideView',
    'PausedPlaylistSlideView',
    'RepeatPlaylistSlideView'
)

# This will give a tuple of tuples of the slideview types.
slideview_types = tuple(slideview._asdict().items())

default_url = '/' # Where we go at the end, e.g., of a playlist hangup.

slide_to_be_launched_attrs = ('experiment', 
                              'ping_uid', 
                              'ping_uid_short', 
                              'slideview_type', 
                              'slideview_kwargs')

SlideToBeLaunched = collections.namedtuple('SlideToBeLaunched', 
                                           slide_to_be_launched_attrs)

live_session_keep_alive_duration = 5 * 60 # Duration in seconds

# No. of seconds until we assume we lost contact with the client
ping_grace_period = 30

error_template = 'presenter/error.html'

feedback_uri = '/feedback'

PLAY_EXPERIMENT_ROOT = '/play/'

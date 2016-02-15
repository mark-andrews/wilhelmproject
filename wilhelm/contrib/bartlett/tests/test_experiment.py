"""
Functional tests of the `bartlett` contributed package.

"""

from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import datetime
from random import uniform, choice
from time import sleep as wait
import random
import time

#=============================================================================
# Third party imports.
#=============================================================================
from numpy import ceil
from selenium import webdriver
from selenium.webdriver.common.by import By

#=============================================================================
# Django imports.
#=============================================================================
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.template import Context, loader

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.archives.models import Experiment, ExperimentVersion
from apps.core.utils.docutils import rst2innerhtml
from apps.core.utils.strings import fill

from apps.presenter.conf import button, PLAY_EXPERIMENT_ROOT
from apps.sessions.models import ExperimentSession
from apps.subjects.models import Subject
from apps.testing.utils import rndemail, rndpasswd, rndstring
from contrib.bartlett.models import (Playlist, 
                                     SessionPlaylist,
                                     SessionTextDisplay,
                                     SessionTetris,
                                     SessionTextRecallMemoryTest,
                                     SessionTextRecognitionMemoryTest,
                                     SessionWordlistDisplay,
                                     SessionWordlistRecallMemoryTest,
                                     SessionWordlistRecognitionMemoryTest,
                                     SessionWordRecallTest,
                                     SessionWordRecognitionTest,
                                     WordRecognitionTest,
                                     WordRecallTest,
                                     TextDisplay, 
                                     Tetris,
                                     WordlistDisplay)

#=============================================================================
# Local imports.
#=============================================================================
from . import utils
from .utils import (create_experiment, 
                    reset_text_times, 
                    get_inner_html,
                    wait_until_element_not_displayed,
                    wait_until_some_elements_displayed,
                    wait_until_element_displayed,
                    all_visible,
                    none_visible)

#================================ End Imports ================================


class ExperimentTestCase(StaticLiveServerTestCase):

    text_display_widget_tested = False
    wordlist_display_widget_tested = False

    def tearDown(self):

        self.driver.quit()
        print('Wordlist display slide tested. %d' %
              self.wordlist_display_widget_tested)

        print('Text display slide tested. %d' %
              self.text_display_widget_tested)
   
    def setUp(self):

        (self.experiment_name, 
         self.experiment_class_name, 
         self.experiment_title) = create_experiment()

        self.driver = webdriver.Firefox()
        self.driver.maximize_window()
        self.implicit_wait = 0.0
        self.driver.implicitly_wait(self.implicit_wait)

    def wilhelmlogout(self):

        self.driver.get(self.live_server_url)
        self.driver.find_element_by_class_name('sign-out')\
            .find_element_by_link_text('Sign out').click()


    def wilhelmlogin(self, username, password):

        return utils.wilhelmlogin(self.driver, 
                                  self.live_server_url, 
                                  username,
                                  password)

    #=============================================================================
    # Testing helper functions.
    #=============================================================================
    def _test_signup_new_user(self):

        """
        Create a new user and log them in.

        """

        self.username = rndemail()
        first_name = rndstring(10)
        password = rndpasswd(10)

        user = User.objects.create_user(username=self.username,
                                        first_name=first_name,
                                        email=self.username,
                                        password=password)

        Subject.objects.create_subject(user)

        signed_in_as = self.wilhelmlogin(self.username, password)

        self.assertIn(self.username, signed_in_as.text)

    def _test_get_experiment(self):

        experiment=\
            Experiment.objects.get(class_name = self.experiment_class_name)\
            .current_version

        # Just make sure the model are what they should be.
        self.assertEquals(experiment.name, self.experiment_name)
        self.assertIs(type(experiment), ExperimentVersion)

        return experiment


    def _test_get_experiment_playlist(self):

        experiment = self._test_get_experiment()

        # Check that playlist is a Playlist
        self.assertIs(type(experiment.playlist), Playlist)

        return experiment.playlist

    
    def _test_get_experiment_instructions(self):

        playlist = self._test_get_experiment_playlist()

        self.assertTrue(hasattr(playlist, 'instructions'))

        self.assertIs(type(playlist.instructions), list)

        return playlist.instructions


    def get_current_playlist_session(self):

        """

        Check and return the current playlist session.

        """

        user = User.objects.get(username = self.username)
        subject = Subject.objects.get(user = user)

        experiment_sessions\
            = ExperimentSession.objects.get_all_my_experiment_sessions(subject)

        # Should be just one.
        self.assertEquals(len(experiment_sessions), 1)

        experiment_session = experiment_sessions[0]

        self.assertEqual(type(experiment_session.playlist_session),
                         SessionPlaylist)

        # Get the playlist session
        playlist_session = experiment_session.playlist_session

        # Current session slide ought to be one of these.
        self.assertIn(type(playlist_session.current_slide),
                      (SessionWordlistRecognitionMemoryTest,
                       SessionWordlistRecallMemoryTest,
                       SessionTextRecognitionMemoryTest,
                       SessionTextRecallMemoryTest))

        return playlist_session


    def get_current_widgets(self):

        """

        Check and return the two widgets and session widgets from the current
        slide.

        """

        playlist_session = self.get_current_playlist_session()

        # Get the session widgets of the first session slide.
        session_widgets = playlist_session.current_slide.get_session_widgets()

        widgets\
            = tuple([session_widget.widget for session_widget in session_widgets])

        self.assertTrue(len(session_widgets), 2)

        # First has to be a wordlist display or text display.
        self.assertIn(type(session_widgets[0]),
                      (SessionWordlistDisplay, 
                       SessionTextDisplay))

        self.assertIn(type(widgets[0]), 
                      (TextDisplay, WordlistDisplay))

        # Second has to be Tetris
        self.assertEqual(type(session_widgets[1]), SessionTetris)
        self.assertEqual(type(widgets[1]), Tetris)

        # Third has to be a wordlist display or text display.
        self.assertIn(type(session_widgets[2]),
                      (SessionWordRecallTest, 
                       SessionWordRecognitionTest))

        self.assertIn(type(widgets[2]), 
                      (WordRecallTest, WordRecognitionTest))

        return widgets, session_widgets

    #=========================================================================
    # Tests
    #=========================================================================

    def test_experiment_listing_page(self):

        """
        Can we bring up the Brisbane experiment page?

        """


        self._test_signup_new_user()

        self.driver.get(self.live_server_url + '/experiments')

        self.assertEquals('Experiment List', self.driver.title)

        experiment_listings\
            = self.driver.find_elements_by_class_name('experiment-listing')

        self.assertEqual(len(experiment_listings), 
                         len(Experiment.objects.all())
                         )

        self.wilhelmlogout()

    def test_follow_experiment_link(self):

        """
        Can we bring up the Brisbane experiment page by clicking?

        """

        self._test_signup_new_user()

        self.driver.get(self.live_server_url + '/experiments')

        experiment_listings\
            = self.driver.find_elements_by_class_name('experiment-listing')

        experiment_listing = experiment_listings[0]

        experiment_listing\
            .find_element_by_tag_name('h2')\
            .find_element_by_tag_name('a').click()

        self.assertEquals('Experiment: {0}'.format(self.experiment_title), 
                          self.driver.title)

        self.driver.get(self.live_server_url)

        self.wilhelmlogout()


    def test_follow_experiment_url(self):

        self._test_signup_new_user()

        self.driver.get(
            self.live_server_url + PLAY_EXPERIMENT_ROOT + '{0}'.format(self.experiment_name)
        )

        self.assertEquals('Experiment: {0}'.format(self.experiment_title), 
                          self.driver.title)

        self.driver.get(self.live_server_url)

        self.wilhelmlogout()

    def test_instructions(self):

        """
        Test if the instructions are correct and are displayed properly, i.e.
        one page at a time.

        """

        def test_is_instruction_page_displayed(instruction_pages, 
                                               displayed=(True, False, False)):
            """
            A convenience function to test which instructions page is currently
            being displayed.

            """

            for instruction_page, page_displayed in zip(instruction_pages, 
                                                   displayed):

                self.assertEquals(instruction_page.is_displayed(),
                                  page_displayed)

        def test_is_button_displayed(buttons, displayed=(True, False, False)):

            """
            A convenience function to test which button is displayed.

            """
            
            for button, button_displayed in zip(buttons, displayed):

                self.assertEquals(button.is_displayed(),
                                  button_displayed)

        #=====================================================================
        # Retrieve the true instructions from the Playlist model.
        #=====================================================================
        instructions = self._test_get_experiment_instructions()

        rendered_instructions\
            = [rst2innerhtml(instruction) for instruction in instructions]

        #=====================================================================
        # Get the instructions list from the webpage.
        #=====================================================================
        self._test_signup_new_user()

        self.driver.get(
            self.live_server_url + PLAY_EXPERIMENT_ROOT + '{0}'.format(self.experiment_name)
        )

        wait(1.0)

        instruction_items\
            = self.driver.find_element_by_class_name('InstructionBox')\
            .find_element_by_tag_name('ol')\
            .find_elements_by_tag_name('li')

        # Do we have the correct number of instructions?
        self.assertEqual(len(instruction_items),
                         len(rendered_instructions))

        # Is the content of the instructions correct?
        for instruction_item, rendered_instruction\
                in zip(instruction_items, rendered_instructions):

            self.assertEquals(instruction_item.get_attribute('innerHTML'), 
                              rendered_instruction)

        # Is only the first page actually displayed?
        test_is_instruction_page_displayed(instruction_items, 
                                           (True, False, False))

        # Are there three buttons?
        #    = self.driver.find_element_by_class_name('ButtonBox')\
        #    .find_elements_by_class_name('button')

        buttons\
            = self.driver.find_element_by_id('instructions-nav-buttons')\
            .find_elements_by_class_name('button')


        self.assertEqual(len(buttons), 3)

        # Are they Previous, Next and Start Experiment, in that order?
        for button, label in zip(buttons, 
                                 ['Previous', 'Next', 'Start Experiment']):
            self.assertEqual(button.get_attribute('innerHTML'), label)

        # But only Next is visible?
        test_is_button_displayed(buttons, (False, True, False))

        #=====================================================================
        # Walk through the instructions pages.
        #=====================================================================

        def click_next():
            self.driver.find_element_by_id('next-instruction').click()
            wait(0.5)

        def click_previous():
            self.driver.find_element_by_id('previous-instruction').click()
            wait(0.5)

        # Forward one page ...
        click_next()

        # Now is only the second page displayed?
        test_is_instruction_page_displayed(instruction_items, 
                                           (False, True, False, False))

        # The Previous and Next buttons should be displayed.
        test_is_button_displayed(buttons, (True, True, False))


        # Forward one more page ...
        click_next()

        # Now is only the third page displayed?
        test_is_instruction_page_displayed(instruction_items, 
                                           (False, False, True, False))

        # The Previous and Start Experiment buttons should be displayed.
        test_is_button_displayed(buttons, (True, True, False))

        # Back one page ...
        click_previous()

        # Now is only the second page displayed?
        test_is_instruction_page_displayed(instruction_items, 
                                           (False, True, False, False))

        # The Previous and Next buttons should be displayed.
        test_is_button_displayed(buttons, (True, True, False))

        # Back one more page ...
        click_previous()

        # Now is only the first page displayed?
        test_is_instruction_page_displayed(instruction_items, 
                                           (True, False, False, False))

        # Only the Previous button should be displayed.
        test_is_button_displayed(buttons, (False, True, False))

        #=====================================================================
        # A random walk through the instructions pages.
        #=====================================================================
        page_and_button_display_conditions\
            = (((True, False, False, False), (False, True, False)),
               ((False, True, False, False), (True, True, False)),
               ((False, False, True, False), (True, True, False)),
               ((False, False, False, True), (True, False, True)))

        def test_page_and_buttons(page=0):

            page_display, button_display\
                = page_and_button_display_conditions[page]

            test_is_instruction_page_displayed(instruction_items, 
                                               page_display)

            test_is_button_displayed(buttons, button_display)

        def forward(page=0):

            if page < 3:
                wait(0.5)
                click_next()
                page +=1
                test_page_and_buttons(page)

            return page

        def back(page=2):

            if page > 0:
                wait(0.5)
                click_previous()
                page -=1
                test_page_and_buttons(page)

            return page

        page = 0
        for _ in xrange(100):
            movement = random.choice([forward, back])
            page = movement(page)

        self.driver.get(self.live_server_url)
        self.wilhelmlogout()

    def get_session_widgets(self):

        """
        Get the session widgets of the first session slide.

        """

        user = User.objects.get(username = self.username)
        subject = Subject.objects.get(user = user)

        experiment_sessions\
            = ExperimentSession.objects.get_all_my_experiment_sessions(subject)

        experiment_session = experiment_sessions[0]

        # Get the playlist session
        playlist_session = experiment_session.playlist_session

        return playlist_session.current_slide.get_session_widgets()


    def get_first_slide_display_widget(self):

        session_widgets = self.get_session_widgets()
        return session_widgets[0].widget

    def get_second_slide_display_widget(self):

        session_widgets = self.get_session_widgets()
        return session_widgets[1].widget

    def start_experiment(self):

        """

        When we get to the start of an experiment, the instructions should be
        visible, the start button should be too, but the StimulusBox should
        not. 

        This "sub-test" can be run at the start of other tests.

        """

        self._test_signup_new_user()

        self.driver.get(
            self.live_server_url + PLAY_EXPERIMENT_ROOT + '{0}'.format(self.experiment_name)
        )

        #=============================================================================
        # Click through the instructions here.
        #=============================================================================

        click_next\
            = self.driver.find_element_by_id('next-instruction').click

        click_next()
        click_next()
        click_next()

        start_button\
            = self.driver.find_element_by_id('instructions-nav-buttons')\
            .find_element_by_id('StartButton')

        start_button.click()

        #=============================================================================

    def get_widget_startbutton(self, widget):

        widgetlist\
            = self.driver.find_element_by_id('widgetlist')

        instruction_box\
            = widget.find_element_by_class_name('InstructionBox')

        startbutton\
            = widget.find_element_by_id('StartButton')

        stimulus_box\
            = widget.find_element_by_id('StimulusBox')

        self.assertFalse(instruction_box.is_displayed())
        self.assertTrue(widgetlist.is_displayed())
        self.assertFalse(startbutton.is_displayed())
        self.assertTrue(stimulus_box.is_displayed())

        return startbutton

#    def test_start_experiment_first_widget_instructions(self):
#
#        """
#        When we get to the start of an experiment, the instructions should be
#        visible, the start button should be too, but the StimulusBox should
#        not. 
#
#
#        """
#
#        #widgetlist, instruction_box, start_button, stimulus_box\
#        self.start_experiment()
#
#        #=====================================================================
#        # Test if the instructions are displayed properly 
#        #=====================================================================
#
#        session_widgets = self.get_session_widgets()
#
#        widget = session_widgets[0].widget 
#        instruction_box\
#            = widget.find_element_by_class_name('InstructionBox')
#
#        if type(widget) is TextDisplay:
#
#            template\
#                = loader.get_template('bartlett/TextDisplay.html')
#
#            context = Context(
#                dict(widget_template_data=widget.get_widget_template_data)
#            )
#
#        elif type(widget) is WordlistDisplay:
#
#            template\
#                = loader.get_template('bartlett/WordlistDisplay.html')
#
#            context = Context(
#                dict(widget_template_data=widget.get_widget_template_data)
#            )
#
#        else:
#            self.fail()
#
#        rendered_template = template.render(context)
#
#        self.assertEqual(
#            fill(get_inner_html(rendered_template, 'InstructionBox')),
#            fill(instruction_box.get_attribute('innerHTML').strip())
#        )
#
#        #=====================================================================
#        #=====================================================================
#
#        self.driver.get(self.live_server_url)
#        self.wilhelmlogout()
#
#    def test_start_experiment_click_start(self):
#
#        """
#        After you click start, the instruction box and start button should
#        dissappear and the stimulus box should appear.
#
#        We should see a text being displayed or a wordlist being displayed.
#
#        Run the same test multiple times because of the random choices.
#
#        """
#
#        for _ in xrange(5):
#
#            widgetlist, instruction_box, start_button, stimulus_box\
#                = self.start_experiment()
#
#            start_button.click()
#
#            wait(1)
#
#            self.assertTrue(widgetlist.is_displayed())
#            self.assertFalse(instruction_box.is_displayed())
#            self.assertFalse(start_button.is_displayed())
#            self.assertTrue(stimulus_box.is_displayed())
#
#            wait(1)
#
#            widget = self.get_first_slide_display_widget()
#
#            if type(widget) is TextDisplay:
#
#                stimulus_display_box\
#                    = self.driver.find_element_by_id('textdisplay_box')
#
#                # We do have this from above, but we can get it again (to be safe)
#                stimulus_box\
#                    = stimulus_display_box.find_element_by_id('StimulusBox')
#
#                text_box = stimulus_box.find_element_by_id('text_box')
#                move_box = stimulus_box.find_element_by_id('move_box')
#
#                self.assertTrue(stimulus_display_box.is_displayed())
#                self.assertTrue(text_box.is_displayed())
#                self.assertFalse(move_box.is_displayed())
#                
#            elif type(widget) is WordlistDisplay:
#
#                stimulus_display_box\
#                    = self.driver.find_element_by_id('wordlist_box')
#
#                # We do have this from above, but we can get it again (to be safe)
#                stimulus_box\
#                    = stimulus_display_box.find_element_by_id('StimulusBox')
#
#                word_box = stimulus_box.find_element_by_id('word_box')
#
#                self.assertTrue(stimulus_display_box.is_displayed())
#                self.assertTrue(word_box.is_displayed())
#     
#            else:
#                self.fail()
#            
#
#            self.driver.get(self.live_server_url)
#            self.wilhelmlogout()

    def tic(self):

        self.start = time.time()

    def toc(self):

        try:
            return time.time() - self.start
        except:
            return None

    #######################

    # These are *HACKS* to get the test_stimuli_display test to run again
    # with different starting slides....
    # ... but tearing down and setting up as per usual

    def test_stimuli_display_worddisp_again(self):

        if self.wordlist_display_widget_tested:
            print('Wordlist display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_textdisp_again(self):

        if self.text_display_widget_tested:
            print('Test display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_worddisp_again_i(self):

        if self.wordlist_display_widget_tested:
            print('Wordlist display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_textdisp_again_i(self):

        if self.text_display_widget_tested:
            print('Test display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_worddisp_again_ii(self):

        if self.wordlist_display_widget_tested:
            print('Wordlist display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_textdisp_again_ii(self):

        if self.text_display_widget_tested:
            print('Test display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_worddisp_again_iii(self):

        if self.wordlist_display_widget_tested:
            print('Wordlist display slide tested. True')
        else:
            self.test_stimuli_display()

    def test_stimuli_display_textdisp_again_iii(self):

        if self.text_display_widget_tested:
            print('Test display slide tested. True')
        else:
            self.test_stimuli_display()

    #######################
    def test_stimuli_display(self):

        minimum_time = int(uniform(3, 10))
        maximum_time = int(uniform(12, 20))

        reset_text_times(minimum_time, maximum_time)

        self.start_experiment()

        slide_number = 0

        widgets, session_widgets = self.get_current_widgets()

        element_labels = ('textdisplay_widget', 'wordlist_widget')

        wait_until_some_elements_displayed(self.driver,
                                           element_labels=element_labels,
                                           timeout=20.0)

        start_button\
            = self.driver.find_element_by_id('widget-start-button')\
            .find_element_by_id('StartButton')

        start_button.click()

        ### Widget 1 ###

        if type(widgets[0]) is TextDisplay:

            self.text_display_widget_tested\
                = self.subtest_textdisplay(session_widgets[0],
                                           minimum_time,
                                           maximum_time)

        elif type(widgets[0]) is WordlistDisplay:

            self.wordlist_display_widget_tested\
                = self.subtest_wordlistdisplay(session_widgets[0])

        else:

            self.fail('Neither TextDisplay nor WordlistDisplay')

        ### Widget 2 ###

        element_labels = ('tetris_widget',)

        wait_until_some_elements_displayed(self.driver,
                                           element_labels=element_labels,
                                           timeout=3.0)

        wait(3)

        self.assertEquals(type(widgets[1]), Tetris) 
        self.subtest_tetris(session_widgets[1])

        if type(widgets[2]) is WordRecognitionTest:

            self.subtest_wordrecognitionwidget()

        elif type(widgets[2]) is WordRecallTest:

            self.subtest_wordrecallwidget()

        else:
            self.fail('Should be word recognition test or recall test')
        
        wait(10)

        continue_or_stop, continue_or_stop_button\
            = self.subtest_next_slide_page(slide_number)

        wait(3)

        continue_or_stop_button.click()

        wait(10)

        self.driver.get(self.live_server_url)
        self.wilhelmlogout()

         # ALLDONE = True

#        if ALLDONE:
#            break

#    def old_test_stimuli_display(self): # delete this
#
#        iteration = 0
#
##        while not (text_display_widget_tested and
##                   wordlist_display_widget_tested and iteration > 10):
##
#        iteration += 1
#
#        minimum_time = int(uniform(3, 10))
#        maximum_time = int(uniform(12, 20))
#
#        reset_text_times(minimum_time, maximum_time)
#
#        self.start_experiment()
#
#        slide_number = 0
#
#        #while True:
#
#        widgets, session_widgets = self.get_current_widgets()
#
#        element_labels = ('textdisplay_widget', 'wordlist_widget')
#
#        wait_until_some_elements_displayed(self.driver,
#                                           element_labels=element_labels,
#                                           timeout=20.0)
#
#        start_button\
#            = self.driver.find_element_by_id('widget-start-button')\
#            .find_element_by_id('StartButton')
#
#        start_button.click()
#
#        #wait(3.0)
#
#
#        ### Widget 1 ###
#
#        if type(widgets[0]) is TextDisplay:
#
#            self.text_display_widget_tested\
#                = self.subtest_textdisplay(session_widgets[0],
#                                           minimum_time,
#                                           maximum_time)
#
#        elif type(widgets[0]) is WordlistDisplay:
#
#            self.wordlist_display_widget_tested\
#                = self.subtest_wordlistdisplay(session_widgets[0])
#
#        else:
#
#            self.fail('Neither TextDisplay nor WordlistDisplay')
#
#        ### Widget 2 ###
#
#        element_labels = ('recognitiontest_widget', 'recalltest_widget')
#
#        wait_until_some_elements_displayed(self.driver,
#                                           element_labels=element_labels,
#                                           timeout=3.0)
#
#        wait(3)
#
#        self.assertEquals(type(widgets[1]), Tetris) 
##
##        if type(widgets[1]) is WordRecognitionTest:
##
##            self.subtest_wordrecognitionwidget()
##
##        elif type(widgets[1]) is WordRecallTest:
##
##            self.subtest_wordrecallwidget()
##
##        else:
##        
#        wait(3)
#
#        continue_or_stop, continue_or_stop_button\
#            = self.subtest_next_slide_page(slide_number)
#
#        slide_number += 1
#
#        wait(3)
#
#        continue_or_stop_button.click()
#
#        if continue_or_stop == 'stop':
#            pass
#            #break 
#
#        wait(10)
#
#        self.driver.get(self.live_server_url)
#        self.wilhelmlogout()
#
#         # ALLDONE = True
#
##        if ALLDONE:
##            break
#
    #=========================================================================
    # Widget sub-tests.
    #=========================================================================
    def subtest_textdisplay(self, session_widget, minimum_time, maximum_time):

        self.assertEquals(type(session_widget.widget), 
                          TextDisplay)

        self.assertEquals(type(session_widget), 
                          SessionTextDisplay)

        stimulus_display_box\
            = self.driver.find_element_by_id('textdisplay_widget')
   
        stimulus_box\
            = stimulus_display_box.find_element_by_id('StimulusBox')

        text_box = stimulus_box.find_element_by_id('text_box')
        text_p_box = text_box.find_element_by_id('text_p_box')
        title_box = text_box.find_element_by_id('title_box')

        #startbutton = self.get_widget_startbutton(stimulus_display_box)
        #startbutton.click()

        wait_until_element_displayed(self.driver, 'text_p_box')

        self.assertEqual(text_p_box.text,
                         session_widget.widget.text)

        self.assertEqual(title_box.text,
                         session_widget.widget.title)

        move_box = stimulus_box.find_element_by_id('move_box')

        self.assertTrue(text_box.is_displayed())
        self.assertFalse(move_box.is_displayed())
        
        self.tic()

        wait_until_element_displayed(self.driver, 
                                     element_label='move_box',
                                     timeout=minimum_time*2)

        self.assertLessEqual(minimum_time,
                             ceil(self.toc())
                             )

        wait_until_element_not_displayed(self.driver, 
                                         'move_box',
                                         timeout=(maximum_time-minimum_time)*2)

        self.assertLessEqual(maximum_time,
                             ceil(self.toc())
                             )

        self.assertFalse(move_box.is_displayed())

        wait_until_element_not_displayed(self.driver, 
                                         element_label='text_box',
                                         timeout=1.0)

        self.assertFalse(text_box.is_displayed())

        return True

    def subtest_tetris(self, session_widget):

        self.assertEquals(type(session_widget.widget), 
                          Tetris)

        self.assertEquals(type(session_widget), 
                          SessionTetris)

        stimulus_display_box\
            = self.driver.find_element_by_id('tetris_widget')

        extra_instructions\
            = stimulus_display_box.find_element_by_id('tetris-extra-instructions')
       
        instruction_box\
            = stimulus_display_box.find_element_by_class_name('InstructionBox')

        startbutton\
            = stimulus_display_box.find_element_by_id('StartButton')

        stimulus_box\
            = stimulus_display_box.find_element_by_id('StimulusBox')

        gameover_box\
            = stimulus_display_box.find_element_by_id('GameOver')

        gamebox\
            = stimulus_display_box.find_element_by_id('gamebox')


        self.assertTrue(stimulus_display_box.is_displayed())
        self.assertFalse(extra_instructions.is_displayed())
        self.assertTrue(instruction_box.is_displayed())
        self.assertTrue(startbutton.is_displayed())
        self.assertFalse(stimulus_box.is_displayed())
        self.assertFalse(gameover_box.is_displayed())
        self.assertFalse(gamebox.is_displayed())

 
        wait(3)
        startbutton.click()
        wait(3)

        self.assertTrue(gamebox.is_displayed())


        wait(30)

#        self.assertEqual(text_p_box.text,
#                         session_widget.widget.text)
#
#        self.assertEqual(title_box.text,
#                         session_widget.widget.title)
#
#        move_box = stimulus_box.find_element_by_id('move_box')
#
#        self.assertTrue(text_box.is_displayed())
#        self.assertFalse(move_box.is_displayed())
#        
#        self.tic()
#
#        wait_until_element_displayed(self.driver, 
#                                     element_label='move_box',
#                                     timeout=minimum_time*2)
#
#        self.assertLessEqual(minimum_time,
#                             ceil(self.toc())
#                             )
#
#        wait_until_element_not_displayed(self.driver, 
#                                         'move_box',
#                                         timeout=(maximum_time-minimum_time)*2)
#
#        self.assertLessEqual(maximum_time,
#                             ceil(self.toc())
#                             )
#
#        self.assertFalse(move_box.is_displayed())
#
#        wait_until_element_not_displayed(self.driver, 
#                                         element_label='text_box',
#                                         timeout=1.0)
#
#        self.assertFalse(text_box.is_displayed())

        return True




    def subtest_wordlistdisplay(self, session_widget):

        self.assertEquals(type(session_widget.widget), 
                          WordlistDisplay)

        self.assertEquals(type(session_widget), 
                          SessionWordlistDisplay)

        wordlist = [session_widget.widget.wordlist[i] 
                    for i in session_widget.wordlist_permutation]

        wordlist_box\
            = self.driver.find_element_by_id('wordlist_widget')

        #startbutton = self.get_widget_startbutton(wordlist_box)
        #startbutton.click()

        for i, word in enumerate(wordlist):

            wait_until_element_displayed(self.driver,
                                         element_label='memory_word')

            memory_word = self.driver.find_element(By.ID,
                                                   'memory_word')

            self.assertEqual(memory_word.text, word)

            wait_until_element_not_displayed(self.driver,
                                             element_label='memory_word')

            self.assertEqual(memory_word.text, '')

        return True


    def subtest_next_slide_page(self, slide_number):

        next_slide_xpath =  "//div[@id='next_slide']"
        
        next_slide_message_box\
            = next_slide_xpath + "/div[@class='MessageBox']"

        end_of_slide_form\
            = next_slide_xpath + "/div[@id='EndOfSlideForm']"

        continue_button\
            = end_of_slide_form + "/div[@id='ContinueButton']"

        pause_button\
            = end_of_slide_form + "/div[@id='PauseButton']"

        stop_button\
            = end_of_slide_form + "/div[@id='StopButton']"

        always_visible_elements =  (next_slide_xpath, 
                                    next_slide_message_box, 
                                    end_of_slide_form)

        visible_elements = [(continue_button, pause_button), 
                            (continue_button, pause_button),
                            (stop_button,) ]

        invisible_elements = [
            (stop_button,), 
            (stop_button,), 
            (continue_button, pause_button)
        ]

        self.assertTrue(
            all_visible(self.driver, 
                        always_visible_elements + visible_elements[slide_number])
        )

        self.assertTrue(
            none_visible(self.driver, invisible_elements[slide_number])
        )


        template\
            = loader.get_template('presenter/live_experiment_launcher.html')
        
        slide_context\
            = [dict(slides_done=1, 
                    experiment_name = 'brisbane',
                  slides_remaining=2, 
                  button=button), 
               dict(slides_done=2,
                    experiment_name = 'brisbane',
                    slides_remaining=1,
                    button=button), 
               dict(slides_done=3,
                    experiment_name = 'brisbane',
                    slides_remaining=0,
                    button=button)]

        #context = Context(slide_context[slide_number])
        #rendered_template = template.render(context)
        rendered_template = template.render(slide_context[slide_number])
            
        self.assertEqual(
            fill(get_inner_html(rendered_template, 'MessageBox')),
            fill(self.driver.find_element_by_xpath(next_slide_message_box)\
                 .get_attribute('innerHTML').strip())
        )

#
#        message_texts = (
#        [
#            'You have finished Part 1 of the experiment "brisbane".',
#            'There are 2 parts remaining.',
#            'To continue the experiment now, '\
#            +'you can press the "{0}" button.'.format(button.next),
#            'To continue later, '\
#            +'you can press the "{0}" button.'.format(button.pause)
#        ],
#        [
#            'You have finished Part 2 of the experiment "brisbane".',
#            'There is 1 part remaining.',
#            'To continue the experiment now, '\
#            +'you can press the "{0}" button.'.format(button.next),
#            'To continue later, '\
#            +'you can press the "{0}" button.'.format(button.pause)
#        ],
#        [
#            'You have finished Part 3 of the experiment "brisbane".',
#            'The experiment is now over.'
#        ])


#        for text in message_texts[slide_number]:
#            self.assertIn(text,
#                          self.driver.find_element_by_xpath(next_slide_message_box).text)
#

        if slide_number < 2:
            return 'continue', self.driver.find_element_by_xpath(continue_button)
        else: 

            return 'stop', self.driver.find_element_by_xpath(stop_button)


    def subtest_wordrecognitionwidget(self):

        recognitiontest_box_xpath\
            = "//div[@id='recognitiontest_widget']"

        start_box_xpath\
            = recognitiontest_box_xpath + "//div[@id='StartBox']"

        instruction_box_xpath\
            = start_box_xpath + "/div[@id='InstruxtionBox']"

        start_button_xpath\
            = start_box_xpath + "//span[@id='StartButton']"

        stimulus_box_xpath\
            = recognitiontest_box_xpath + "//div[@id='StimulusBox']"

        stimulus_tag_xpath\
            = stimulus_box_xpath + "/div[@id='StimulusTag']"

        word_box_xpath\
            = stimulus_tag_xpath + "/div[@id='word_box']"

        test_word_xpath\
            = word_box_xpath + "//span[@id='test_word']"

        response_box_xpath\
            = stimulus_tag_xpath + "/div[@id='response_box']"

        present_button_xpath\
            = response_box_xpath + "/span[@id='present_button']"
        
        absent_button_xpath\
            = response_box_xpath + "/span[@id='absent_button']"

        self.assertTrue(
            all_visible(self.driver,
                        (recognitiontest_box_xpath,
                         start_box_xpath,
                         instruction_box_xpath,
                         start_button_xpath))
        )


        self.assertTrue(
            none_visible(self.driver,
                         (word_box_xpath,
                         stimulus_box_xpath,
                         word_box_xpath,
                         present_button_xpath,
                         absent_button_xpath,
                         response_box_xpath))
        )

        self.driver.find_element_by_xpath(start_button_xpath).click()
        wait(1.0)

        self.assertTrue(
            all_visible(self.driver,
                        (recognitiontest_box_xpath,
                         stimulus_box_xpath,
                         word_box_xpath,
                         present_button_xpath,
                         absent_button_xpath,
                         response_box_xpath))
        )

        self.assertTrue(
            none_visible(self.driver,
                         (start_box_xpath,
                         instruction_box_xpath,
                         start_button_xpath))
        )

        present_button\
            = self.driver.find_element_by_xpath(present_button_xpath)
        absent_button\
            = self.driver.find_element_by_xpath(absent_button_xpath)

        presentation_widget, game_widget, response_widget = self.get_session_widgets()

        wordlist_permutation = response_widget.wordlist_permutation

        wordlist_with_expected_responses\
            = [response_widget.widget.wordlist_with_expected_responses[i] 
                    for i in wordlist_permutation]
        

        random_actions = {'click_present': present_button.click,
                          'click_absent': absent_button.click, 
                          'skip': lambda : None}
        actions = []

        hits = []
        wordlist = []
        expected_responses = []
        responses = []
        response_latencies = []
        accuracies = []

        for i, word_with_expected_response in enumerate(wordlist_with_expected_responses):

            word, expected_response = word_with_expected_response

            element = wait_until_element_displayed(self.driver,
                                                   test_word_xpath,
                                                   attribute_type='xpath')


            self.assertEqual(element.text, word)

            self.assertTrue(
                all_visible(self.driver,
                             (test_word_xpath,
                              present_button_xpath,
                              absent_button_xpath))
            )


            action_label, action = choice(random_actions.items())
            print(action_label)

            actions.append(action_label)

            wait(2)
            self.tic()
            action()

            element = wait_until_element_not_displayed(self.driver,
                                                       test_word_xpath,
                                                       attribute_type='xpath')
            self.assertEqual(element.text, "")

            toc = self.toc()
            timeout = response_widget.widget.timeOutDuration


            self.assertTrue(
                none_visible(self.driver,
                             (test_word_xpath,
                              present_button_xpath,
                              absent_button_xpath))
            )

            if action_label == 'skip':

                # TODO (Fri 21 Aug 2015 14:35:26 BST): Fix this.
                if i>0: # This is a hack. Timer on first action is always wrong
                    # because of bad code above.
                         self.assertTrue(timeout - 2.0 < toc < timeout + 2.0,
                                    msg = 'Not True: %2.2f < %2.2f < %2.2f'\
                                    % (timeout - 2.0, toc, timeout + 2))

                hit = False
                accuracy = None
                response_latency = None
                response = None
            else:

                self.assertLess(toc, 1.0)

                response_latency = toc
                hit = True
                response = action_label == 'click_present'
                accuracy = response == expected_response

            hits.append(hit)
            wordlist.append(word)
            expected_responses.append(expected_response)
            accuracies.append(accuracy)
            responses.append(response)
            response_latencies.append(response_latency)

        wait(10)

        self.assertEqual(wordlist, response_widget.response_items)
        
        response_data_denormalized\
            = response_widget.response_data_denormalized

        for i, response_data in enumerate(response_data_denormalized):

            (word, 
             expected_response, 
             response_latency, 
             response, 
             accuracy, 
             hit, 
             order) = map(response_data.get,
                        ('stimulus_word', 
                         'expected_response', 
                         'response_latency',
                         'response',
                         'response_accuracy',
                         'hit',
                         'order'))

            print("Checking %s." % word)

            self.assertEqual(word, wordlist[i])
            self.assertEqual(expected_response, expected_responses[i])
            #self.assertEqual(response_latency, response_latencies[i])
            self.assertEqual(response, responses[i])
            self.assertEqual(hit, hits[i])
            self.assertEqual(accuracy, accuracies[i])
            self.assertEqual(i, order)

        print("line 1288. completed is %s" % response_widget.completed)
        print("Showing denormalized word recognition data.")
        print(response_widget.response_data_denormalized)
        print(response_widget.data_export())
        print("line 1292. completed is %s" % response_widget.completed)

    def subtest_wordrecallwidget(self):

        recallmemorytest_box_xpath\
            = "//div[@id='recalltest_widget']"

        start_box_xpath\
            = recallmemorytest_box_xpath + "//div[@id='StartBox']"

        instruction_box_xpath\
            = start_box_xpath + "/div[@id='InstruxtionBox']"

        start_button_xpath\
            = start_box_xpath + "//span[@id='StartButton']"

        stimulus_box_xpath\
            = recallmemorytest_box_xpath + "//div[@id='StimulusBox']"

        recalledwords_box_xpath\
            = stimulus_box_xpath + "//div[@id='recalledwordsbox']"

        recalledwordslist_box_xpath\
            = recalledwords_box_xpath + "//ol[@id='recalledwordslist']"

        morelessoptions_xpath\
            = recalledwords_box_xpath + "//div[@id='morelessoptions']"

        lessoptions_xpath\
            = morelessoptions_xpath + "/span[@id='lessoptionsbutton']"

        moreoptions_xpath\
            = morelessoptions_xpath + "/span[@id='moreoptionsbutton']"

        results_box\
           = recalledwords_box_xpath + "//div[@id='results']"

        submit_results_box\
            = results_box + "/span[@id='submitresults']"

        finish_box_xpath\
            = recallmemorytest_box_xpath + "//div[@id='FinishBox']"

        finish_msg_xpath\
            = finish_box_xpath + "/p[@id='FinishMsg']"


        self.assertTrue(
            all_visible(self.driver,
                        (recallmemorytest_box_xpath,
                         start_box_xpath,
                         instruction_box_xpath,
                         start_button_xpath))
        )


        self.assertTrue(
            none_visible(self.driver,
                         (stimulus_box_xpath,
                          recalledwords_box_xpath,
                          morelessoptions_xpath,
                          results_box,
                          submit_results_box,
                          finish_box_xpath,
                          finish_msg_xpath,
                          recalledwordslist_box_xpath))
        )

        self.driver.find_element_by_xpath(start_button_xpath).click()

        wait(5)

        self.assertTrue(
            all_visible(self.driver,
                         (recallmemorytest_box_xpath,
                          stimulus_box_xpath,
                          recalledwords_box_xpath,
                          results_box,
                          submit_results_box,
                          morelessoptions_xpath,
                          lessoptions_xpath,
                          moreoptions_xpath,
                          recalledwordslist_box_xpath))
        )

        self.assertTrue(
            none_visible(self.driver,
                        (start_box_xpath,
                         instruction_box_xpath,
                         finish_msg_xpath, 
                         finish_box_xpath,
                         start_button_xpath))
        )


        items\
            = self.driver.find_element_by_xpath(recalledwordslist_box_xpath)\
            .find_elements_by_tag_name('li')

        # TODO (Fri 29 May 2015 03:28:32 BST): Deal with this
        magic_number = 10 

        self.assertEqual(len(items), magic_number)

        less_button = self.driver.find_element_by_xpath(lessoptions_xpath)
        more_button = self.driver.find_element_by_xpath(moreoptions_xpath)

        less_button.click()

        items\
            = self.driver.find_element_by_xpath(recalledwordslist_box_xpath)\
            .find_elements_by_tag_name('li')

        self.assertEqual(len(items), magic_number-1)

        less_button.click()

        items\
            = self.driver.find_element_by_xpath(recalledwordslist_box_xpath)\
            .find_elements_by_tag_name('li')

        self.assertEqual(len(items), magic_number-2)

        more_button.click()

        items\
            = self.driver.find_element_by_xpath(recalledwordslist_box_xpath)\
            .find_elements_by_tag_name('li')

        self.assertEqual(len(items), magic_number-1)

        more_button.click()

        items\
            = self.driver.find_element_by_xpath(recalledwordslist_box_xpath)\
            .find_elements_by_tag_name('li')

        self.assertEqual(len(items), magic_number)

        random_words = []
        for item in items[:random.randint(1, len(items)-1)]:
            input_box = item.find_element_by_tag_name('input')
            random_word = rndstring(random.randint(3, 10))
            input_box.send_keys(random_word)
            random_words.append(random_word)

        wait(2)

        self.driver.find_element_by_xpath(submit_results_box).click()

        wait_until_element_displayed(self.driver, 
                                     finish_msg_xpath,
                                     attribute_type='xpath')

        self.assertTrue(
            all_visible(self.driver,
                        (finish_msg_xpath, finish_box_xpath))
        )

        items\
            = self.driver.find_element_by_xpath(finish_box_xpath)\
            .find_element_by_tag_name('ol')\
            .find_elements_by_tag_name('li')

        self.assertEqual(len(items), len(random_words))

        for random_word, item in zip(random_words, items):
            self.assertEqual(random_word, item.text)

        presentation_widget, game_widget, response_widget\
            = self.get_session_widgets()

        self.assertEqual(random_words, response_widget.recalledwords)

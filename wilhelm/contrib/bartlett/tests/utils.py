import os

#=============================================================================
# Third party imports.
#=============================================================================
from selenium.webdriver.common.by import By
import BeautifulSoup
import configobj, validate
import selenium.webdriver.support.ui as ui
from selenium.common.exceptions import NoSuchElementException

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core.utils import python, strings
from apps.archives.models import (Experiment, 
                                  ExperimentVersion,
                                  ExperimentArchive,
                                  ExperimentRepository)

from contrib.bartlett.models import TextDisplay
 
#================================ End Imports ================================

this_dir = os.path.abspath(os.path.dirname(__file__))

repository_settings_filename = 'settings.cfg'
repository_experiments_modulename = 'experiments'
repository_settings_configspec = '''
    [experiments]
    [[__many__]]
    include = list(default=None)
    release-note = string(default='The latest version.')'''.strip().split('\n')


def create_experiment():

    experiment_name = 'brisbane'

    experiment_title = experiment_class_name = 'Brisbane'

    experiment_archive = os.path.join(this_dir, 'experiment_repository')

    experiments_module= python.impfromsource(
        repository_experiments_modulename, experiment_archive
    )

    experiments_settings = os.path.join(experiment_archive,
                                        repository_settings_filename)

    config = configobj.ConfigObj(
        experiments_settings,
        configspec = repository_settings_configspec
        )

    validator = validate.Validator()

    assert config.validate(validator, copy=True)

    for class_name, experiment_notes in config['experiments'].items():

        label = class_name + 'foobaz123456789'

        release_note = experiment_notes['release-note']

        playlist_factory = getattr(experiments_module, class_name)

        playlist = playlist_factory.new()

        fake_repository\
            = ExperimentRepository.objects.create(name = 'fake_repo')
        fake_archive\
            = ExperimentArchive.objects.create(repository=fake_repository,
                                               commit_hash=strings.uid())

        blurb = ' '.join(""" In this experiment, your memory for word lists
                         or short texts will be tested.  For example, you
                         could be shown a list of words and then asked to
                         recall as many as you can. Or you could be asked
                         to read a short text and then asked if certain
                         words occurred or not. There are six parts to this
                         experiment and each part will take around 3-5
                         minutes.  """.split())

        title = 'Memory for texts and word lists'

        experiment\
            = Experiment.objects.create(class_name=class_name,
                                        live=True,
                                        title = title,
                                        blurb=blurb)

        ExperimentVersion.new(
            experiment=experiment,
            label=label,
            release_note=release_note,
            playlist=playlist,
            archive=fake_archive)

    return experiment_name, experiment_class_name, experiment_title

def reset_text_times(minimum_reading_time, maximum_reading_time):

    for text in TextDisplay.objects.all():
        text.minimum_reading_time = minimum_reading_time
        text.maximum_reading_time = maximum_reading_time

        text.save()


# TODO (Sun 17 May 2015 18:00:07 BST): This function should be moved to a
# central location, e.g., testing.
def wilhelmlogin(driver, live_server_url, username, password):

    driver.get(live_server_url + '/login')

    username_element = driver.find_element_by_name('username')
    password_element = driver.find_element_by_name('password')

    username_element.send_keys(username)
    password_element.send_keys(password)

    driver.find_element_by_id('login').submit()

    signed_in_as = driver.find_element_by_class_name('signed-in-as')\
        .find_element_by_class_name('username')

    return signed_in_as


def get_inner_html(html, div_class):

    """
    Get the inner html of the div with class `class`.
    """

    soup = BeautifulSoup.BeautifulSoup(html)

    div = soup.find("div", { "class" : div_class })

    return u''.join(map(str, div.contents)).strip()

class Element(object):

    """
    To facilitate tests of whether page elements are displayed.

    Adapted from http://stackoverflow.com/a/25029769/1009979

    """

    attribute_types\
        = {"id":"ID",
           "xpath":"XPATH",
           "link text":"LINK_TEXT",
           "partial link text":"PARTIAL_LINK_TEXT",
           "name":"NAME",
           "tag name":"TAG_NAME",
           "class name":"CLASS_NAME",
           "css selector":"CSS_SELECTOR"}

    def __init__(self, element_label, attribute_type='id'):

        self.by_attribute\
            = getattr(By, self.attribute_types[attribute_type])

        self.element_label = element_label

    def exists(self, driver):
        try:
           self.element(driver)
           return True
        except NoSuchElementException:
            return False

    def is_displayed(self, driver):
        try:
           return self.element(driver).is_displayed()
        except NoSuchElementException:
            return False

    def element(self, driver):
        return driver.find_element(self.by_attribute, self.element_label)
        
def wait_until_element_display_status(driver, 
                                      element_label, 
                                      display_status=True,
                                      attribute_type='id',
                                      timeout=10):

    element = Element(element_label, attribute_type)
    
    condition = lambda _driver: element.is_displayed(_driver) == display_status

    ui.WebDriverWait(driver, timeout).until(condition)

    return element.element(driver)

def wait_until_element_displayed(driver, 
                                 element_label, 
                                 attribute_type='id',
                                 timeout=10):

    display_status = True

    return wait_until_element_display_status(driver, 
                                             element_label, 
                                             display_status,
                                             attribute_type,
                                             timeout)


def wait_until_element_not_displayed(driver, 
                                     element_label, 
                                     attribute_type='id',
                                     timeout=10):

    display_status = False

    return wait_until_element_display_status(driver, 
                                             element_label, 
                                             display_status,
                                             attribute_type,
                                             timeout)

  
def wait_until_some_elements_displayed(driver, 
                                       element_labels, 
                                       attribute_type='id',
                                       timeout=10):

    elements = [Element(element_label, attribute_type) 
                for element_label in element_labels]
    
    condition = lambda _driver: any(
        [element.is_displayed(_driver) for element in elements]
    )

    return ui.WebDriverWait(driver, timeout).until(condition)


def test_visibility(driver, element_labels, test_function):

    elements = [Element(element_label, attribute_type='xpath')
                for element_label in element_labels]

    return test_function([element.is_displayed(driver) for element in elements])


def all_visible(driver, element_labels):

    test_function = all

    return test_visibility(driver, element_labels, test_function)
 
def some_visible(driver, element_labels):

    test_function = any

    return test_visibility(driver, element_labels, test_function)

def none_visible(driver, element_labels):

    test_function = lambda elements: not any(elements)

    return test_visibility(driver, element_labels, test_function)
 

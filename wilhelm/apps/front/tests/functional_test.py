from django.test import LiveServerTestCase
from selenium import webdriver

class WelcomeTest(LiveServerTestCase):

    def setUp(self): #
        self.browser = webdriver.Chrome()

    def tearDown(self): #
        self.browser.quit()

    def test_welcome_page(self): #
        self.browser.get(self.live_server_url)
        self.assertIn('Cognition Experiments', self.browser.title) #

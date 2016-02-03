from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import datetime
import os
from random import choice, randint
import string

#=============================================================================
# Django imports.
#=============================================================================
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User

#=============================================================================
# Wilhelm imports 
#=============================================================================
from apps.subjects.models import Subject
from apps.subjects.conf import minimal_password_length
from apps.core.utils.strings import msg

#=============================================================================
# Third party imports.
#=============================================================================
from selenium import webdriver

#================================ End Imports ================================
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS']\
    = settings.MAIN_SUBDOMAIN_NAME

fakeuser = dict(firstname = 'Foobar',
                username = 'foo.foobar@gmail.com')

def rndstring(string_length, chars = string.lowercase):

    return ''.join([choice(chars) for _ in xrange(string_length)])


def rndpasswd(password_length, chars = string.letters + string.digits):

    '''
    Make a password of length `password_length` of (by default) randomly chosen
    alpha-numeric characters.

    '''
    
    return rndstring(password_length, chars)


def rndemail(prefix_length = 10, suffix_length = 5):

    prefix = rndstring(prefix_length)
    suffix = rndstring(suffix_length)

    return prefix + '@' + suffix + '.' + choice(['org', 'com', 'net'])

class RandomUser(object):


    def __init__(self):

        self.password = rndpasswd(minimal_password_length + 1)
        self.firstname = rndstring(5).capitalize()
        self.username = rndemail()

        self.birthday = (randint(1960, 1995), randint(1, 12), randint(1, 28))
        self.sex = choice(['male', 'female'])
        self.handedness = choice(['left', 'right'])
        self.english_or_other = choice(['english', 'other'])

        self.other_language = ''

        if self.english_or_other == 'other' and choice([True, False]):
            self.other_language = choice(['French', 'Chinese', 'Spanish' ])


        self.is_right_handed = True if self.handedness == 'right' else False
        self.is_male = True if self.sex == 'male' else False
        self.is_english_speaker = True if self.english_or_other == 'english' else False

class SignUpTestCase(StaticLiveServerTestCase):

    def setUp(self):

        self.driver = webdriver.Firefox()
        self.driver.maximize_window()
        self.driver.implicitly_wait(60)

    def tearDown(self):

        self.driver.quit()

    #=========================================================================
    # Non-testing helper functions.
    #=========================================================================
    def signup_new_user(self, firstname, username, password, confirmpassword):

        '''
        Signup a user with firstname = firstname, username = username, password
        = password, confirmpassword = confirmpassword.

        Put these details into the signup form and press the submit button.
        '''

        self.driver.get(self.live_server_url + '/signup')

        firstname_element = self.driver.find_element_by_name('firstname')
        username_element = self.driver.find_element_by_name('username')
        password_element = self.driver.find_element_by_name('password')
        confirmpassword_element\
            = self.driver.find_element_by_name('confirmpassword')

        signup_btn = self.driver.find_element_by_id('signup')

        firstname_element.send_keys(firstname)
        username_element.send_keys(username)
        password_element.send_keys(password)
        confirmpassword_element.send_keys(confirmpassword)

        signup_btn.submit()

    def login_user(self, username, password):

        self.driver.get(self.live_server_url + '/login')

        username_element = self.driver.find_element_by_name('username')
        password_element = self.driver.find_element_by_name('password')
 
        username_element.send_keys(username)
        password_element.send_keys(password)

        self.driver.find_element_by_id('login').submit()

        signed_in_as = self.driver.find_element_by_class_name('signed-in-as')\
            .find_element_by_class_name('username')

        self.assertIn(username, signed_in_as.text)


    def wilhelmlogout(self):

        self.driver.find_element_by_class_name('sign-out')\
            .find_element_by_link_text('Sign out').click()

    def birthday_selector(self, year, month, day):

        xpath_str = "//select[@name='birth[%s]']/option[@value='%d']" 
        
        month_xpath = xpath_str % ('month', month)
        day_xpath = xpath_str % ('day', day)
        year_xpath = xpath_str % ('year', year)

        for xpath in [month_xpath, day_xpath, year_xpath]:
            self.driver.find_element_by_id('bday')\
                .find_element_by_xpath(xpath).click()

    def select_radio_button(self, element_id, value):

        """
        Click the radio button in ``element_id`` with value ``value``.


        """

        xpath = ".//input[@type='radio' and @value='%s']" % value

        return self.driver.find_element_by_id(element_id)\
            .find_element_by_xpath(xpath).click()

    def select_demographics(self, 
                            birthday, 
                            sex, 
                            handedness, 
                            english_or_other, 
                            other_language):

        self.birthday_selector(*birthday)
        self.select_radio_button('sex-pick', sex)
        self.select_radio_button('handedness-pick', handedness)
        self.select_radio_button('native_language-pick', english_or_other)

        if english_or_other == 'other':
            self.driver.find_element_by_id('other_language_box')\
                .send_keys(other_language)

        self.driver.find_element_by_id('demographics_submit').submit()
    #=========================================================================


    #=========================================================================
    # Testing helper functions
    #=========================================================================
    def _test_frontpage_signed_in_as(self, username):

        self.assertEquals('Cognition Experiments', self.driver.title)

        signed_in_as = self.driver.find_element_by_class_name('signed-in-as')\
            .find_element_by_class_name('username')

        self.assertIn(username, signed_in_as.text)



    def test_pageload_test_title(self):

        '''
        For a set of urls, check the urls resolve and load pages and that their
        titles are correct.

        '''

        # TODO (Mon Apr 13 16:06:57 2015): Some of these pages are not part of
        # the subjects app so should be tested in other apps.
        pages_and_titles = [('/login', 'Member Login'),
                            ('/signup', 'Sign up'),
                            ('/forgotpassword', 'Forgot Password'),
                            ('/experiments', 'Experiment List'),
                            ('/listing', 'Experiment List'),
                            ('', 'Cognition Experiments'),
                            ('/about', 'Cognition Experiments'),
                            ('/takingpart', 'Cognition Experiments'),
                            ('/privacy', 'Cognition Experiments')]

        for page, title in pages_and_titles:
            self.driver.get(self.live_server_url + page)
            self.assertEqual(title, self.driver.title)

    def test_signup_new_user(self):

        '''
        Test that we can sucessfully sign up a new subject.

        Succesful signup includes a redirect to the front page, and an update
        of the User and Subject model.

        '''
        
        self.assertFalse(User.objects.all())

        password = rndpasswd(minimal_password_length + 1)

        self.signup_new_user(password=password,
                             confirmpassword=password, 
                             **fakeuser)

        # TODO (Sat 11 Jul 2015 21:17:20 BST): After signup, we are redirected to the
        # experiment launcher, not the main front page. We need to fix this.
        # self.assertEquals('Cognition Experiments', self.driver.title)

        signed_in_as = self.driver.find_element_by_class_name('signed-in-as')\
            .find_element_by_class_name('username')

        self.assertIn(fakeuser['username'], signed_in_as.text)
        
        self.assertEqual(len(User.objects.all()), 1)

        new_user = User.objects.get(username = fakeuser['username'])

        self.assertEqual(new_user.first_name, fakeuser['firstname'])
        self.assertTrue(new_user.check_password(password))

        self.assertEqual(len(Subject.objects.all()), 1)

        subject = Subject.objects.all()[0]
        self.assertEqual(subject.user, new_user)

        self.assertFalse(subject.social_media_login)
        self.assertEqual(subject.login_method, 'wilhelm')

    def test_user_demographic(self):


        for _ in xrange(5):
            random_user = RandomUser()

            self.signup_new_user(password = random_user.password,
                                 confirmpassword = random_user.password, 
                                 firstname = random_user.firstname,
                                 username = random_user.username)

            self.wilhelmlogout()

            self.login_user(random_user.username, random_user.password)

            self.select_demographics(birthday = random_user.birthday,
                                     sex = random_user.sex,
                                     handedness = random_user.handedness,
                                     english_or_other =
                                     random_user.english_or_other,
                                     other_language = random_user.other_language)


            if (random_user.english_or_other == 'other' 
                    and random_user.other_language == ''):

                error_msg\
                    = self.driver.find_element_by_id('native_language_error')

                self.assertEquals('"Other Language" should not be blank.',
                                  error_msg.text)

            else:

                self._test_frontpage_signed_in_as(random_user.username)

                new_user = User.objects.get(username = random_user.username)

                subject = Subject.objects.get(user=new_user)

                self.assertEqual(subject.date_of_birth,
                                 datetime.date(*random_user.birthday))
         
                self.assertEqual(subject.right_handed,
                                 random_user.is_right_handed)

                self.assertEqual(subject.male, random_user.is_male)

                self.assertEqual(subject.is_english_speaker, 
                                 random_user.is_english_speaker)

                if random_user.is_english_speaker:
                    self.assertEqual(subject.native_language, 'English')
                else:
                    self.assertEqual(subject.native_language,
                                     random_user.other_language)
             
            self.wilhelmlogout()

    def test_block_repeat_signup_attempt(self):

        '''
        Test that an attempt to signup again using the same username (i.e.,
        email address) will be blocked.
        
        '''

        firstname = fakeuser['firstname']
        username = fakeuser['username']
        password = rndpasswd(minimal_password_length + 1)

        self.signup_new_user(password = password,
                             confirmpassword = password,
                             firstname = firstname,
                             username = username)

        self.wilhelmlogout()

        self.signup_new_user(password = password,
                             confirmpassword = password,
                             firstname = firstname,
                             username = username)
        
        expected_error_msg = msg(
        '''An account using the email "%s" already exists. Do you already have an account?''' 
                % (username)
        )

        error_msg_span = self.driver\
            .find_element_by_class_name('username-error')

        self.assertIn(expected_error_msg, error_msg_span.text)

    def test_user_login(self):

        '''
        Test that an existing user can login.

        '''

        password = rndpasswd(minimal_password_length + 1)
        self.signup_new_user(password = password,
                             confirmpassword = password,
                             **fakeuser)

        self.wilhelmlogout()

        for iteration in xrange(3):

            self.driver.get(self.live_server_url + '/login')

            username_element = self.driver.find_element_by_name('username')
            password_element = self.driver.find_element_by_name('password')
     
            username_element.send_keys(fakeuser['username'])
            password_element.send_keys(password)

            self.driver.find_element_by_id('login').submit()

            signed_in_as = self.driver.find_element_by_class_name('signed-in-as')\
                .find_element_by_class_name('username')

            self.assertIn(fakeuser['username'], signed_in_as.text)

            self.wilhelmlogout()

    def test_catch_blank_firstname(self):

        ''' 
        Test that in the signup form, the subject's firstname is not blank.
        
        '''

        email = fakeuser['username']
        password = rndpasswd(minimal_password_length + 1)

        expected_error_msg = 'First name should not be empty.'

        self.signup_new_user(firstname = '',
                             username = email,
                             password = password,
                             confirmpassword = password)

        error_msg_span = self.driver\
            .find_element_by_class_name('firstname-live-error')

        self.assertIn(expected_error_msg, error_msg_span.text)

    def test_catch_blank_username(self):

        '''
        Test that in the signup form, the subject's username (email address) is
        not blank. 

        '''

        firstname = fakeuser['firstname']
        password = rndpasswd(minimal_password_length + 1)

        expected_error_msg = 'Email address should not be empty.'

        self.signup_new_user(firstname = firstname,
                             username = '',
                             password = password,
                             confirmpassword = password)

        error_msg_span = self.driver\
            .find_element_by_class_name('username-live-error')

        self.assertIn(expected_error_msg, error_msg_span.text)

    def test_catch_bad_email_address(self):

        '''
        Test that email addresses conform to the specified regular expression,
        i.e., more or less "something@somewhere.suffix".

        '''

        firstname = fakeuser['firstname']
        password = rndpasswd(minimal_password_length + 1)

        expected_error_msg = 'That email address does not look valid.'

        for username in ['foobaz', 'foo@baz', 'foo.org', 'foo@org']:

            self.signup_new_user(firstname = firstname,
                                 username = username,
                                 password = password,
                                 confirmpassword = password)

            error_msg_span = self.driver\
                .find_element_by_class_name('username-live-error')

            self.assertIn(expected_error_msg, error_msg_span.text)

    def test_catch_password_too_short(self):

        '''
        Test that all passwords are as or greater than a minimal length. 

        '''

        firstname = fakeuser['firstname']
        username = fakeuser['username']

        expected_error_msg\
            = 'The password should be at least {0} characters.'\
            .format(minimal_password_length)

        for loop in xrange(10):
            password_length = randint(0, minimal_password_length-1)
            self.signup_new_user(firstname = firstname,
                                 username = username,
                                 password = rndpasswd(password_length),
                                 confirmpassword = 'can_be_anything')

            error_msg_span = self.driver\
                    .find_element_by_class_name('password-live-error')

            self.assertIn(expected_error_msg, error_msg_span.text)

    def test_catch_passwords_do_not_match(self):

        '''
        Subjects must re-enter their proposed password. Test that we can catch
        any password mismatches.

        '''

        password = rndpasswd(minimal_password_length + 1)
        confirmpassword = rndpasswd(minimal_password_length + 2)

        self.signup_new_user(password=password,
                             confirmpassword=confirmpassword,
                             **fakeuser)

        password_live_error\
          = self.driver.find_element_by_class_name('check-password-live-error')

        self.assertIn('Passwords do not match', password_live_error.text)

    def test_login_via_social_media(self):

        '''
        Test if subjects can login in from their Facebook or Google+ accounts.

        '''

        # Details for Twitter, in case they are needed again.
        # ('btn-twitter', 'username_or_email', 'password', 'allow')]
        # ('@testingwilhelm', 'O0)Nu2^c', 'testingwilhelm')]

        SocialMedia = dict()

        SocialMedia['Facebook']\
            = (('btn-facebook', 'email', 'pass', 'u_0_2'),
               ('testing.wilhelmproject@gmail.com', 'a)9Ft0|O', 'WilhelmTester')
               )

        SocialMedia['Google']\
            = (('btn-google', 'Email', 'Passwd', 'signIn'),
               ('testing.wilhelmproject@gmail.com', ']aCe0U^7', 'testing.wilhelmproject')
               )


        for i, key in enumerate(SocialMedia):

            api, account = SocialMedia[key]
        
            btn, username_tag, passwd_tag, signin_tag = api
            username, password, identity = account

            self.driver.get(self.live_server_url + '/signup')
            self.driver.find_element_by_class_name(btn).click()

            if key == 'Google':
                username_object = self.driver.find_element_by_id(username_tag)
                username_object.send_keys(username)

                next_btn = self.driver.find_element_by_id('next')
                next_btn.submit()

                password_object = self.driver.find_element_by_id(passwd_tag)
                password_object.send_keys(password)

                login_btn = self.driver.find_element_by_id(signin_tag)
                login_btn.submit()
            else:
                username_object = self.driver.find_element_by_id(username_tag)
                password_object = self.driver.find_element_by_id(passwd_tag)

                username_object.send_keys(username)
                password_object.send_keys(password)

                login_btn = self.driver.find_element_by_id(signin_tag)
                login_btn.submit()

            signed_in_as\
                = self.driver.find_element_by_class_name('signed-in-as')\
                .find_element_by_class_name('username')

            self.assertIn(identity, signed_in_as.text)

            # Test User and Subject database.

            self.assertEqual(len(User.objects.all()), i+1)

            self.assertEqual(len(Subject.objects.all()), i+1)

            user = User.objects.get(username = identity)
            subject = Subject.objects.get(user = user)

            self.assertEqual(user.email, username)
            self.assertEqual(subject.user.email, username)

            self.assertTrue(subject.social_media_login)
            self.assertTrue(subject.login_method in ['facebook',
                                                     'google-oauth2'])

            self.wilhelmlogout()

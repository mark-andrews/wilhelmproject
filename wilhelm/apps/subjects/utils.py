from __future__ import absolute_import, print_function

#=============================================================================
# Standard library imports
#=============================================================================
import logging
import traceback
import sys

#=============================================================================
# Django imports
#=============================================================================
from django.core.mail import send_mail
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import authenticate, login

#=============================================================================
# Wilhelm imports
#=============================================================================
from . import conf
from .models import Subject
from apps.core.utils.datetime import strptime
from apps.core.utils.strings import msg, rpassword
from apps.core.utils.django import (user_does_not_exist, 
                                    user_exists,
                                    reset_password)

#=============================================================================
# Other imports.
#=============================================================================
from validate_email import validate_email

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')

def dump_traceback():

    exception_type, exception_value, exception_traceback\
        = sys.exc_info()
    exception_details = str(exception_type.__name__) + " : " + str(exception_value)
    traceback_details = '\n'.join(traceback.format_tb(exception_traceback))

    print(exception_details, file=sys.stderr)
    print(traceback_details, file=sys.stderr)

    return exception_details

def list_all_nontemp_subjects():
    '''
    Return a list of strings that provide details of each non-temp subject.
    '''

    sex = {True: 'Male',
           False: 'Female'}

    S = []

    for subject in Subject.objects.all():

        if not subject.temp_subject:

            details = (('email', subject.user.username), 
                       ('name', subject.user.first_name),
                       ('sex', sex[subject.male]),
                       ('age', subject.age)
                      )

            sep = '\n' + ' ' * 4

            s = sep.join(
                ['[{0}]'.format(subject.uid[:settings.UID_SHORT_LENGTH])]
                +
                ['{0} = {1}'.format(key,value) for key, value in details]
            )

            S.append(s)

    return S

def subject_enroll(enroll_cfg):
    '''
    The enroll_cfg should be configobj parsed file. 

    '''

    subjects = []

    for email, details in enroll_cfg.items():

        userdict = dict(username = email,
                        email = email,
                        first_name = details['first_name'].title(),
                        password = details['password'],
                        male = bool(details['male']),
                        dob = strptime(details['dob'], '%Y-%m-%d')
                        )

        try:
            user = User.objects.get(username=userdict['username'])
            subject = Subject.objects.get(user=user)

            if not user.check_password(userdict['password']):
                user.set_password(userdict['password'])
                user.save()

            if not user.first_name == userdict['first_name']:
                user.first_name = userdict['first_name']
                user.save()

            for key in ['male', 'dob']:
                if not getattr(subject, key) == userdict[key]:
                    setattr(subject, key, userdict[key])

 
        except ObjectDoesNotExist:

            user = User.objects.create_user(username=userdict['username'],
                                            password=userdict['password'],
                                            first_name=userdict['first_name'],
                                            email=userdict['email'])
            user.validate_unique()
            user.save()
            
            subject = Subject.objects.create_subject(user,
                                                     date_of_birth=userdict['dob'],
                                                     male=userdict['male'])

        subjects.append((user, subject))

    return subjects

def enroll_demo_subject():
    return User.objects.create_user(username = conf.demo_username,
                                    password = conf.demo_user_password)

def is_demo_account(request):
    ''' Is request.user authenticated and the demo account user?'''
    assert request.user.is_authenticated()
    return request.user.username == conf.demo_username

def get_subject_from_request(request):
    ''' For normal subjects, there is a one to one map from users to subjects.
    For demo accounts, it is not as simple: There are many temporary subjects
    for one demo account. The browser session should have a key
    "temp_subject_uid" and this will give you the temporary subject for the
    demo account in the current browser session.  '''

    if is_demo_account(request):

        assert 'temp_subject_uid' in request.session

        subject\
            = Subject.objects.get(uid = request.session['temp_subject_uid'])

        assert subject.temp_subject,\
            'The demo user should have a temp subject account.'

    else:
        user = request.user
        subject = Subject.objects.get(user=user)

    return subject

def has_unlimited_experiment_attempts(request):
    '''
    Does request.user have unlimited attempts at all experiments?
    '''

    if settings.UNLIMITED_EXPERIMENT_ATTEMPTS:
        return True
    else:

        if is_demo_account(request):
            return True
        else:
            return False

def social_media_user_subject_create(**kwargs):

    '''
    Create the Subject instance for a new user who has logged in via social
    media.

    '''

    try:

        user = kwargs.pop('user')

        try:

            Subject.objects.get(user=user)

        except ObjectDoesNotExist:

            subject = Subject.objects.create_subject(user)

            try:
                backend = kwargs['backend']
                login_method = backend.name
            except (KeyError, AttributeError) :
                login_method = 'Unknown social media login backend'
                logger.warning(login_method)

            subject.login_method = login_method
            subject.save()

            logger.info('Created new subject for user=%s. Login via %s.'\
                        % (subject.user.username, login_method))

    except KeyError:    

        logger.warning('No user object returned from social media login pipeline.')


def wilhelmlogin(request, username, password):

        user = authenticate(username=username, 
                            password=password)

        assert user is not None,\
            msg('The username or password you entered is incorrect.')

        assert user.is_active, msg('Your account is not active.')

        login(request, user)

        if is_demo_account(request):
            subject = Subject.objects.create_temp_subject(user)
            request.session['temp_subject_uid'] = subject.uid
        else:
            subject = Subject.objects.get(user=user)

        return user, subject

class SignUpForm(object):

    @classmethod
    def process(cls, request):
        '''
        Use: valid, feedback = SignUpForm.process(postdict)
        '''

        signupform = cls(request)

        valid = True
        feedback = dict()

        try:
            username_and_email = signupform.getusername()
        except AssertionError as e:
            valid = False
            feedback['username_error_msg'] = e.message

        try:
            password = signupform.getpassword()
        except AssertionError as e:
            valid = False
            feedback['password_error_msg'] = e.message

        try:
            first_name = signupform.getfirstname()
        except AssertionError as e:
            valid = False
            feedback['firstname_error_msg'] = e.message

        if valid:

            try:

                user = User.objects.create_user(username=username_and_email,
                                                first_name=first_name,
                                                email=username_and_email,
                                                password=password)

                subject = Subject.objects.create_subject(user)

            except (IntegrityError, AssertionError) as e:
                valid = False
                feedback['create_subject_error_msg'] = e.message

            try:

                logged_in_user, logged_in_subject\
                    = wilhelmlogin(request, username_and_email, password)

                assert user == logged_in_user
                assert subject == logged_in_subject
                assert subject.user == user

                logger.info('New subject %s successfully logged in.'\
                            % subject.user.username)

            except Exception as e:

                error_message = 'Could not log in new subject.'

                feedback['create_subject_error_msg'] = error_message
                logger.warning(error_message)

        if valid:

            feedback['first_name'] = first_name
            feedback['email'] = username_and_email
            feedback['uid'] = subject.uid
 
        else:

           for placeholder_key, postdict_key in (
                   ('username_starting_value', 'username'), 
                   ('firstname_starting_value', 'firstname'),
                   ('password_starting_value', 'password'),
                   ('confirmpassword_starting_value', 'confirmpassword'),
           ):

                if signupform.postdict[postdict_key]:
                    feedback[placeholder_key]\
                        = signupform.postdict[postdict_key]

        return valid, feedback


    def __init__(self, request):

        self.postdict = request.POST

    def getusername(self):

        emailaddr = self.postdict['username'].strip()
        assert len(emailaddr), 'Email address should not be empty'
        assert validate_email(emailaddr), 'Invalid email address.'
        assert user_does_not_exist(emailaddr), msg('''
                An account using the email "%s" already exists. Do you already
                have an account?
                ''' % emailaddr)

        return emailaddr

    def getpassword(self):

        password = self.postdict['password']
        confirmpassword = self.postdict['confirmpassword']

        assert len(password) >= conf.minimal_password_length,\
            'Password should be at least %d chars.' % int(conf.minimal_password_length)
        assert password == confirmpassword, 'The passwords do not match.'

        return password

    def getfirstname(self):

        first_name = self.postdict['firstname'].strip()
        assert len(first_name), 'First name should not be empty.'

        return first_name.title()

class ForgotPasswordForm(object):

    @classmethod
    def process(cls, request):

        forget_password_form = cls(request)
        valid = True
        feedback = {}

        try:
            forget_password_form.getuser()
        except AssertionError as e:
            valid = False
            feedback['username_error_msg'] = e.message

        if valid:
            new_password_email_msg = forget_password_form.reset_password()
            feedback['first_name'] = forget_password_form.user.first_name
            user_email_address = forget_password_form.user.username
                        
            try:
                send_mail('%s password reset' % settings.WILHELMPROJECTNAME,
                          new_password_email_msg,
                          from_email=settings.WEBMASTEREMAIL,
                          recipient_list=[user_email_address])
                feedback['reset_password_success'] = True
                feedback['reset_password_sent_to_email'] = user_email_address
            except Exception as e:
                valid = False
                feedback['send_mail_failure'] = True
                feedback['send_mail_msg_error']\
                    = 'We could not send email to %s. Error message is %s.' % \
                    (user_email_address, e.message)
        else:

            for placeholder_key, postdict_key in (
                    ('username_starting_value', 'username'), 
            ):

                if forget_password_form.postdict[postdict_key]:
                    feedback[placeholder_key]\
                        = forget_password_form.postdict[postdict_key]



        return valid, feedback

    def __init__(self, request):

        self.request = request
        self.postdict = request.POST
        self.username = self.postdict['username']

    def getuser(self):

        emailaddr = self.username.strip()
        assert len(emailaddr), 'Email address should not be empty'
        assert validate_email(emailaddr), 'Invalid email address.'
        assert user_exists(emailaddr), msg('''
                An account using the email "%s" does not exist. Are you sure
                you have an account?
                ''' % emailaddr)

        self.user = User.objects.get(username=emailaddr)

    def reset_password(self):

        new_password = rpassword(conf.minimal_password_length + 2)
        reset_password(self.user, new_password)

        new_password_email\
            = conf.reset_password_email.format(self.user.first_name, 
                                               new_password, 
                                               settings.WWWURL + '/login',
                                               self.user.username,
                                               settings.WEBMASTEREMAIL,
                                               settings.WILHELMPROJECTNAME)

        return new_password_email


class DemographicsForm(object):

    class FormProcessingError(Exception):
        '''
        Custom Exception for form processing errors.
        '''
        def __init__(self, message):
            self.message = message
        def __str__(self):
            return repr(self.message)

    @classmethod
    def process(cls, request, variables):

        '''
        Use: valid, feedback = DemographicsForm.process(postdict)
        '''

        subject = get_subject_from_request(request)

        form = cls(request)

        valid = True
        demographic_info = dict()
        feedback = dict()

        # Safer than using variables directly from function args.
        variables = [key for key in form.processors if key in variables]

        for variable in variables:

            form_processor = form.processors[variable][0]

            try:

                demographic_info[variable] = form_processor()

            except form.FormProcessingError as e:

                valid = False
                feedback[variable + '_error_msg'] = e.message
                logger.warning('Demographic form. Variable %s. Error %s.'
                    % (variable, e.message)
                )

        if valid:

            for variable, value in demographic_info.items():

                model_setter = form.processors[variable][1]
                model_setter(subject, value)

            logger.info('DemographicsForm for Subject %s: Valid.' % subject.user)

        else:
            logger.warning('DemographicsForm for Subject %s: InValid.' % subject.user)

            for placeholder_key, postdict_key in (
                   ('Date_of_Birth_placeholder', 'birthdate'), 
                   ('Handedness_placeholder', 'handedness'), 
                   ('Sex_placeholder', 'sex'), 
                   ('Native_Language_placeholder', 'native_language'),
                   ('Other_Language_placeholder', 'other_language'), 
            ):

                if postdict_key in form.postdict:
                    feedback[placeholder_key] = form.postdict[postdict_key]

        return valid, feedback

    def __init__(self, request):

        self.postdict = request.POST

        self.processors\
            = {'Date_of_Birth': (self.get_birthdate, self.set_birthdate),
               'Sex': (self.get_sex, self.set_sex),
               'Handedness': (self.get_handedness, self.set_handedness),
               'Native_Language': (self.get_native_language,
                                   self.set_native_language)
            }

    #=========================================================================
    # Get data from forms.
    #=========================================================================
    def get_birthdate(self):
        '''
        Return birth date as %Y-%m-%d.
        '''

        return strptime(self.postdict['birthdate'], '%Y-%m-%d')

    def get_sex(self):
        '''
        Return True if sex == 'male'.
        '''

        if self.postdict['sex'] == 'male':
            return True
        elif self.postdict['sex'] == 'female':
            return False

    def get_handedness(self):
        '''
        Return True if handedness == 'right'.
        '''

        if self.postdict['handedness'] == 'right':
            return True
        elif self.postdict['handedness'] == 'left':
            return False

    def get_native_language(self):
        '''
        Return tuple (is_english_speaker, Language), where is_english_speaker
        is a Boolean and Language is the name of the native language. If
        is_english_speaker is True, Language is English.
        '''

        if self.postdict['native_language'] == 'english':
            is_english_speaker, native_language = True, 'English'
        elif self.postdict['native_language'] == 'other':
            is_english_speaker = False
            native_language = self.postdict['other_language']

            if native_language == '':
                raise self.FormProcessingError(
                    '"Other Language" should not be blank.'
                )

        return (is_english_speaker, native_language)

    #=========================================================================
    # Set model's values.
    #=========================================================================
    def set_birthdate(self, subject, value):

        subject.date_of_birth = value
        subject.save()

    def set_sex(self, subject, value):

        subject.male = value
        subject.save()

    def set_handedness(self, subject, value):

        subject.right_handed = value
        subject.save()

    def set_native_language(self, subject, value):

        subject.is_english_speaker, subject.native_language = value
        subject.save()

class LoginForm(object):

    @classmethod
    def process(cls, request):

        loginform = cls(request)

        valid = True
        feedback = {}

        try:
            loginform.login()
        except AssertionError as e:

            valid = False
            feedback['login_error_msg'] = e.message

            for placeholder_key, postdict_key in (
                    ('username_starting_value', 'username'), 
                    ('password_starting_value', 'password'),
            ):

                if loginform.postdict[postdict_key]:
                    feedback[placeholder_key]\
                        = loginform.postdict[postdict_key]


        return valid, feedback

    def __init__(self, request):

        self.request = request
        self.postdict = request.POST
        self.username = request.POST['username']
        self.password = request.POST['password']

    def login(self):

        return wilhelmlogin(self.request,
                            username = self.username,
                            password = self.password)

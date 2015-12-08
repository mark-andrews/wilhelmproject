from __future__ import absolute_import

#=============================================================================
# Django imports.
#=============================================================================
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist, DisallowedRedirect
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.conf import settings
from django.db import models

#=============================================================================
# Core utils imports.
#=============================================================================
from . import strings

#================================ End Imports ================================
def uid():
    '''
    Return a settings.UID_LENGTH random hex string if settings.UID_LENGTH is
    defined. Else, return the default length random hex string.
    '''
    try:
        return strings.uid(k = settings.UID_LENGTH)
    except AttributeError:
        return strings.uid()


def get_all_child_models(parent_model):

    '''
    Return all child models of a given django model.
    '''

    return filter(lambda model : issubclass(model, parent_model),
                  models.get_models()
    )

def jsonResponse(response):
    '''
    A convenience function that makes a json http response.
    '''
    return HttpResponse(response, 'application/javascript')

def http_response(request, template, context):
    '''
    This may just be identical to django's render_to_response.
    '''

    template = loader.get_template(template)
    context = RequestContext(request, context)
    rendered_template = template.render(context)

    return HttpResponse(rendered_template)

def http_redirect(request, default_url='/'):

    try:
        redirection_url = request.session['redirection_url_stack'].pop()
    except (KeyError, IndexError):
        redirection_url = default_url

    try:
        return HttpResponseRedirect(redirection_url)
    except DisallowedRedirect as e:
        print('Exception: %s.' % e.message)
        return HttpResponseRedirect(default_url)

def push_redirection_url_stack(request, url):

    """
    Push to end of stack (with append) if stack exists. If stack does not
    exist, then create list.

    """

    try:
        request.session['redirection_url_stack'].append(url)
    except KeyError:
        request.session['redirection_url_stack'] = [url]


def update_or_create(model, get_fields, update_fields=None,
                     default_fields=None):
    '''
    Try to find an object in `model` with fields `get_fields`. If you find
    it, then update the fields in `update_fields`. 
    If the object does not exist, create it with the fields from the union
    of get_fields, update_fields and default_fields.
    '''

    if not update_fields:
        update_fields = {} # A dict by default.

    if not default_fields:
        default_fields = {}

    try:
        _object = model.objects.get(**get_fields)

        for field in update_fields:
            setattr(_object, field, update_fields[field])

    except ObjectDoesNotExist:

        get_fields.update(update_fields)
        get_fields.update(default_fields)

        _object = model(**get_fields)

    _object.save()
    return _object

def user_exists(username):

    ''' 
    Return True is user with a username `username` does exist, else
    False.
    '''

    try:
        User.objects.get(username=username)
        return True
    except User.DoesNotExist:
        return False

def user_does_not_exist(username):

    ''' 
    Return True if user with a username `username` does not exist, else
    False.
    '''

    return not user_exists(username)

def reset_password(user, new_password):
    ''' Reset user's password to new_password.'''
    user.set_password(new_password)
    user.save()

# TODO (Wed 25 Feb 2015 23:56:24 GMT): PrgObject and form-view. Reinventing the
# django forms wheel?
class PrgObject(object):
    '''
    Post-redirect-get object.
    '''

    def __init__(self, request):
        self.request = request

    def set(self, key, context):
        self.request.session[key] = context

    def redirect(self, url):
        return HttpResponseRedirect(url)

    def pop(self, key):

        if key in self.request.session:
            context = self.request.session[key]
            del self.request.session[key]

        return context

    def has_key(self, key):
        return key in self.request.session

def form_view(request, 
              template,
              context, 
              process, 
              prgobject_key, 
              url_on_valid, 
              url_on_invalid):

    prgobject = PrgObject(request)

    if request.method == 'POST':

        valid, feedback = process(request)

        context.update(feedback)

        prgobject.set(key = prgobject_key,
                      context = context)

        # TODO (Wed 25 Feb 2015 23:41:58 GMT): Is there a good reason for url_on_valid
        # and url_on_invalid are callables? Can't they just be url strings?
        if valid:
            print('valid')
            print(feedback)
            url = url_on_valid()
            return prgobject.redirect(url)
        else:
            print('invalid')
            print(feedback)
            url = url_on_invalid()
            return prgobject.redirect(url)

    elif request.method == 'GET':

        if prgobject.has_key(prgobject_key):
            context = prgobject.pop(prgobject_key)

        return http_response(request, template, context)

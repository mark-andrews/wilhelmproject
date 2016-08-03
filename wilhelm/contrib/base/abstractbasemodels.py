from __future__ import absolute_import
#=============================================================================
# Standard library imports
#=============================================================================
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.db import models
from django.apps import apps
from django.conf import settings
from django.db.models import Model
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import conf
from .slidewidgettypes import WidgetTypes, SlideTypes
from apps.core.utils import django, collections
from apps.core.models import (OrderedGenericElementToContainerModel,
                              GenericElementToContainerModel)

#================================ End Imports ================================
logger = logging.getLogger('wilhelm')


#=============================================================================
# Widget, Slide and Playlist abstract base models.
#=============================================================================

class WidgetSlidePlaylistModel(Model):

    '''
    An abstract base class for the Widget, Slide and Playlist (abstract base
    class) models. It provides model fields and methods that are common
    to the Widget, Slide and Playlist abstract base class models.
    '''

    #=========================================================================
    # Model fields
    #=========================================================================
    uid = models.CharField(max_length=settings.UID_LENGTH,
                           primary_key=True)

    class Meta:
        abstract = True

    #=========================================================================
    # Instance methods.
    #=========================================================================
    def new_session_model(self):

        '''
        Create a Widget or Slide or Playlist session instance corresponding to
        a  Widget or Slide or Playlist instance.

        We can specify the app and model name of the session model
        corresponding to this model using a tuple named
        `conf.SessionModelName`. If that is not there, look for a model in this
        app with the same name as this class but with "Session" prepended to
        it.

        '''

        app_label = self._meta.app_label

        try: 
            
            SessionModelAppName, SessionModelName = getattr(self,
                                                            conf.SessionModelName)

            SessionModel = apps.get_model(SessionModelAppName or app_label, 
                                          SessionModelName)

        except:

            SessionModelName = 'Session' + self.class_name
            SessionModel = apps.get_model(app_label, SessionModelName)

        return SessionModel.new(self)

    @property
    def class_name(self):
        return self.__class__.__name__


class Widget(WidgetSlidePlaylistModel):

    '''
    The Widget abstract base class.

    - uid: a uid primary key
    - widgettype: a foreign key to the widget's WidgetType

    '''

    class Meta:
        abstract = True

    #=========================================================================
    # Model fields
    #=========================================================================
    widgettype = models.ForeignKey(
                    WidgetTypes,
                    related_name ='%(app_label)s_%(class)s_as_element',
                    null=True
    )


    #=========================================================================
    # Model general attributes.
    #=========================================================================
    widget_type_defaults = dict(
        name = None,
        app_label = None,
        htmltemplate = None,
        jstemplate = None,
        gateway = None,
        cssfiles = tuple(),
        jsfiles = tuple()
        )
    
    #=========================================================================
    # Class methods
    #=========================================================================
    @classmethod
    def new(cls, **kwargs):
        return cls._new(**kwargs)

    @classmethod
    def _new(cls, **kwargs):

        '''
        Get or create a new instance of this widget class.

        '''
        print('callin this')

        widgettype = cls.get_widget_type()

        try:
            
           return cls.objects.select_related().get(widgettype = widgettype,
                                  **kwargs)

        except ObjectDoesNotExist:

           return cls.objects.select_related().create(uid = django.uid(), 
                                     widgettype = widgettype,
                                     **kwargs)

    @classmethod
    def get_widget_type(cls):

        '''
        Using the instance's name, htmltemplate, jstemplate, gateway, cssfiles,
        jsfiles attributes, get the widget type with those attributes.

        '''

        defaults = collections.Bunch(cls.widget_type_defaults)

        base_name = cls.get_base_name()

        name = defaults.name or base_name
        app_label = defaults.app_label or cls._meta.app_label
        htmltemplate = defaults.htmltemplate or base_name + conf.htmltemplate_suffix
        jstemplate = defaults.jstemplate or base_name + conf.jstemplate_suffix
        gateway = defaults.gateway or conf.default_widget_gateway

        cssfiles = tuple(collections.uniquelist(defaults.cssfiles))
        jsfiles = tuple(collections.uniquelist(defaults.jsfiles))

        return WidgetTypes.new(
            name = name,
            app_label = app_label,
            htmltemplate = htmltemplate,
            jstemplate = jstemplate,
            gateway = gateway,
            cssfiles = cssfiles,
            jsfiles = jsfiles
        )

    @classmethod
    def get_base_name(cls):

        '''
        Get the name of the widget model.
        '''

        return cls.__name__

    #=========================================================================
    # Instance methods
    #=========================================================================
    def get_jsobject_names(self):

        return self.widgettype.get_jsobject_names()

    def get_html_template(self):

        return self.widgettype.get_html_template()

    def get_widget_template_data(self):
        return None

    def get_widget_js_object(self):
        '''
        This is a quick an dirty fix to the issue of widget instructions (issue
        703). I will attach another key to the dict coming from the widget
        model type. This key's value is a dict coming from a widget method
        (which returns None by default) that returns information to be rendered
        into the widget's template.
        Rather than piggy-backing on the widget_js_object coming from widget
        model type, we should re-think how we send widget information to the
        template in the first place.
        '''
    

        widget_js_object = self.widgettype.get_widget_js_object()
        widget_js_object['widget_template_data']\
            = self.get_widget_template_data()

        logger.debug(widget_js_object)
        return widget_js_object

    def get_widget_data(self):

        '''
        Return, as a dict, the data needed by client-side widget.
        It requires access the property widget_data. 
        '''

        return dict(gateway = self.gateway,
                    **self.widget_data)

    def post_widget_data(self, data):

        '''
        Parse and store the json data returned by the client-side widget.
        This must be overridden in a subclass.
        '''

        pass


    #=========================================================================
    # Properties
    #=========================================================================
    @property
    def gateway(self):
        return self.widgettype.gateway

    @property
    def name(self):
        return self.widgettype.name

    @property
    def app_label(self):
        return self.widgettype.app_label

    

class Slide(WidgetSlidePlaylistModel):

    '''
    The Slide abstract base class.

    Model fields

    - slide_type: a foreign key to the slide's SlideType

    '''

    class Meta:
        abstract = True

    #=========================================================================
    # Model fields
    #=========================================================================
    slide_type\
        = models.ForeignKey(SlideTypes,
                            related_name ='%(app_label)s_%(class)s_as_element',
                            null=True
    )

    #=========================================================================
    # Model general attributes.
    #=========================================================================
    slide_type_defaults = dict(
        name = None,
        app_label = None,
        htmltemplate = None,
        jstemplate = None,
        cssfiles = tuple(),
        jsfiles = tuple()
    )
    
    #=========================================================================
    # Class methods
    #=========================================================================
    @classmethod
    def _new(cls, **kwargs):

        slide_type = cls.get_slide_type()

        try: 
            
           return cls.objects.select_related().get(slide_type = slide_type,
                                                   **kwargs)

        except ObjectDoesNotExist:

           return cls.objects.select_related().create(uid = django.uid(), 
                                                      slide_type = slide_type,
                                                      **kwargs)

    @classmethod
    def get_slide_type(cls):

        '''
        Using the instance's name, htmltemplate, jstemplate, gateway, cssfiles,
        jsfiles attributes, get the widget type with those attributes.

        '''

        defaults = collections.Bunch(cls.slide_type_defaults)

        base_name = cls.get_base_name()

        app_label = defaults.app_label or cls._meta.app_label
        name = defaults.name or base_name
        htmltemplate = defaults.htmltemplate or conf.default_experiment_template

        cssfiles = tuple(collections.uniquelist(defaults.cssfiles))
        jsfiles = tuple(collections.uniquelist(defaults.jsfiles))

        return SlideTypes.new(
            name = name,
            app_label = app_label,
            htmltemplate = htmltemplate,
            cssfiles = cssfiles,
            jsfiles = jsfiles
        )

    @classmethod
    def get_base_name(cls):

        '''
        Get the name of the slide model.
        '''

        return cls.__name__

    #=========================================================================
    # Instance methods.
    #=========================================================================
    def get_widget_js_objects(self):

        widget_js_objects\
            = [widget.get_widget_js_object() for widget in self.widgets]

        for i, widget_js_object in enumerate(widget_js_objects):

            try:
                widget_js_object['next_in_chain']\
                    = widget_js_objects[i+1]['instance_name']

            except IndexError:

                widget_js_object['next_in_chain'] = None

        return widget_js_objects

    def get_css_js_files(self):

        cssfiles = self.slide_type.get_cssfiles()
        jsfiles = self.slide_type.get_jsfiles()

        for widget in self.widgets:
            cssfiles.extend(widget.widgettype.get_cssfiles())
            jsfiles.extend(widget.widgettype.get_jsfiles())

        return tuple(map(collections.uniquelist, (cssfiles, jsfiles)))
    
    def get_slide_template_data(self):
        ''' This method will be overridden by sub-classes.'''
        return None

    def get_template_data(self):

        cssfiles, jsfiles = self.get_css_js_files()

        return dict(widget_js_objects = self.get_widget_js_objects(),
                    slide_template_data = self.get_slide_template_data(),
                    cssfiles = cssfiles,
                    jsfiles = jsfiles
                 )

class Playlist(WidgetSlidePlaylistModel):

    '''
    The Playlist abstract base class.

    '''

    class Meta:
        abstract = True

    #=========================================================================
    # Class methods.
    #=========================================================================
    @classmethod
    def new(cls, slides):
        '''
        This can be over-ridden in subclasses, but if not, it is just a wrapper
        for _new.
        '''
        return cls._new(slides)

    @classmethod
    def _new(cls, slides):

        '''
        Make a new Playlist instance given the set of slides instances.  This
        function will usually be invoked from within a PlaylistFactory in an
        experiments.py module in a experiments repository.

        It checks if a Playlist instance with this set of slides already
        exists. If it does, it returns it. This allows this function to be
        repeatedly called without leading to an error. It will create the
        Playlist instance if it does not exist, and it will return it if it
        already exists.

        '''

        try:

            matching_playlists\
                = SlideAndPlaylistJoinModel.get_playlists_with_slides(slides)
            
            if len(matching_playlists) == 0:
                raise ObjectDoesNotExist
            elif len(matching_playlists) > 1:
                raise MultipleObjectsReturned
            else:
                return matching_playlists.pop()

        except ObjectDoesNotExist:

            playlist = cls(uid = django.uid())
            playlist.save()

            for k, slide in enumerate(slides):

                SlideAndPlaylistJoinModel.new(container=playlist, 
                                              element=slide)

            return playlist

    #=========================================================================
    # Instance methods.
    #=========================================================================
    def get_slides(self):

        '''
        Filter the SlideAndPlaylistJoinModel by this playlist and return the
        slides as a list.
        '''

        return SlideAndPlaylistJoinModel.objects\
            .get_elements_of_container(self)

    def get_slides_uid(self):

        return SlideAndPlaylistJoinModel.objects\
            .get_elements_uid_of_container(self)

    #=========================================================================
    # Properties.
    #=========================================================================
    @property
    def slides(self):
        return self.get_slides()

#=============================================================================
# The Slide to Playlist join model.
#=============================================================================
class SlideAndPlaylistJoinModel(GenericElementToContainerModel):

    @classmethod
    def get_playlists_with_slides(cls, slides):

        return cls.objects.get_containers_with_elements(slides)

# TODO (Sat 23 Aug 2014 15:20:53 BST): Playlists can have their slides ordered. 
## TODO (Mon 06 Jul 2015 16:09:49 BST):  Is this being used?
#class OrderedSlideAndPlaylistJoinModel(OrderedGenericElementToContainerModel):
#    pass

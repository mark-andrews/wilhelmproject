from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
import os

#=============================================================================
# Third party imports 
#=============================================================================
from BeautifulSoup import BeautifulSoup

#=============================================================================
# Django imports
#=============================================================================
from django.db import models
from django.conf import settings
from django.db.models import Model
from django.template import Context, loader
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

#=============================================================================
# Wilhelm imports.
#=============================================================================
from . import utils
from apps.core import fields
from apps.core.utils import strings, django, datetime

#================================ End Imports ================================

#=============================================================================
# Slide and Widget types models
#=============================================================================

class SlideOrWidgetTypes(Model):

    '''
    A convenience abstract base class. It provides a uid (pk), name, and
    date_initiated field to each of the SlideTypes and WidgetTypes.

    uid: A 40 hex string that is the primary key.
    name: A name for the slide or widget.
    date_initiated: When was is initiated.
    cssfiles: Which cssfiles to include.
    jsfiles: Which jsfiles to include.
    htmltemplate: the template for the slide or widget type.

    '''

    class Meta:
        abstract = True

    uid = models.CharField(primary_key=True,
                           max_length=settings.UID_LENGTH)
    app_label = fields.nameField()
    name = fields.nameField()
    date_initiated = fields.DateTimeField()

    cssfiles = fields.ManyToManyField('CssFiles')
    jsfiles = fields.ManyToManyField('JsFiles')

    htmltemplate = fields.nameField()

    @classmethod
    def new_slide_or_widget(cls, name, app_label, htmltemplate, cssfiles, jsfiles):
        '''
        Create a new slide or widget type with the given name, htmltemplate and
        the included cssfiles and jsfiles.
        '''

        slide_or_widget_type = cls(uid = django.uid(),
                                   htmltemplate = htmltemplate,
                                   name = name,
                                   app_label = app_label,
                                   date_initiated = datetime.now()
                                )

        slide_or_widget_type.save()

        if cssfiles:
            for filepath in cssfiles:
                cssfile = CssFiles.new(filepath=filepath)
                slide_or_widget_type.cssfiles.add(cssfile)

        if jsfiles:
            for filepath in jsfiles:
                jsfile = JsFiles.new(filepath=filepath)
                slide_or_widget_type.jsfiles.add(jsfile)

        return slide_or_widget_type

    @classmethod
    def get_slide_or_widget(cls, kwargs, included_css_js):

        '''
        Attempt to get the slide or widget with the specified attributes.
        '''

        widget_or_slide_type_queryset = cls.objects.select_related().filter(**kwargs)

        widget_or_slide_type_queryset\
            = utils.filter_by_includes(widget_or_slide_type_queryset,
                                        **included_css_js)

        widget_or_slide_types = list(widget_or_slide_type_queryset)
        
        if len(widget_or_slide_types) == 0:
            raise ObjectDoesNotExist
        elif len(widget_or_slide_types) > 1:
            raise MultipleObjectsReturned
        else:
            return widget_or_slide_types.pop()

    def get_cssfiles(self):
        return [cssfile.filepath for cssfile in self.cssfiles.all()]

    def get_jsfiles(self):
        return [jsfile.filepath for jsfile in self.jsfiles.all()]

class WidgetTypes(SlideOrWidgetTypes):

    '''
    The model (table) of widget types. Each row here describes the
    properties of a specific widget type, e.g. TextDisplayWidget,
    WordlistDisplayWidget, etc.

    Apart from inherited fields, each widget type has 

    - A template file for the javascript object.
    - A url to act as gateway for restful api.

    '''

    jstemplate = fields.nameField()
    gateway = fields.nameField()

    @classmethod
    def new(cls, 
            name, 
            app_label,
            htmltemplate, 
            jstemplate,
            gateway,
            cssfiles, 
            jsfiles):


        '''
        Get the widget type that has the attributes specified as arguments. If
        there is no match, then create a this widget type.

        '''

        try:
            
            kwargs = dict(name=name, 
                          htmltemplate = htmltemplate, 
                          jstemplate = jstemplate, 
                          gateway = gateway)

            included_css_js = dict(cssfiles = cssfiles, jsfiles = jsfiles)

            return cls.get_slide_or_widget(kwargs, included_css_js)

        except ObjectDoesNotExist:

            widget_type = cls.new_slide_or_widget(name=name, 
                                                  app_label=app_label,
                                                  htmltemplate=htmltemplate, 
                                                  cssfiles=cssfiles, 
                                                  jsfiles=jsfiles)

            widget_type.jstemplate = jstemplate 
            widget_type.gateway = gateway

            widget_type.save()

            return widget_type

    def getdomtag(self):
        '''
        Return the id of the main div of the html boilerplate.
        '''
        
        soup = BeautifulSoup(self.get_html_template())
        divs = soup.find('div')
        return divs['id']

    def get_arglist(self):

        domtag = "'#" + self.getdomtag() + "'"
        gateway = "'/" + self.gateway + "/" + self.name + "/'"

        return [domtag, gateway, 'ping_uid' ]

    def get_jsobject_names(self):

        '''
        Get the widget's jsobject class name and the name for an instance of
        this class.
        '''

        jsobject_class_name = self.name + 'Object'
        jsobject_instance_name = strings.camelToSnake(jsobject_class_name)

        return jsobject_instance_name, jsobject_class_name

    def get_html_template_name(self):

        return os.path.join(self.app_label,
                            self.name + '.html')

    def get_html_template(self):


        template_name = self.get_html_template_name()
        template = loader.get_template(template_name)

        context = Context()

        return template.render(context)

    def get_widget_js_object(self):

        instance_name, class_name = self.get_jsobject_names()

        return dict(path = self.app_label,
                    name = self.name,
                    template_name = self.get_html_template_name(),
                    instance_name = instance_name,
                    class_name = class_name,
                    args = self.get_arglist()
                    )


class SlideTypes(SlideOrWidgetTypes):

    '''
    Each row of this table is a type of slide, e.g. a
    WordlistRecognitionMemoryTest. 
    '''

    @classmethod
    def new(cls, 
            name, 
            app_label,
            htmltemplate, 
            cssfiles, 
            jsfiles):

        try:

            kwargs = dict(name=name, htmltemplate=htmltemplate)
            included_css_js = dict(cssfiles = cssfiles, jsfiles = jsfiles)

            return cls.get_slide_or_widget(kwargs, included_css_js)

        except ObjectDoesNotExist:

            return cls.new_slide_or_widget(name, 
                                           app_label,
                                           htmltemplate, 
                                           cssfiles=cssfiles, 
                                           jsfiles=jsfiles)

class PlaylistTypes(Model):

    '''
    So far, there really is only one type of playlist. So there is nothing
    here. In fact, this may always remain empty.

    '''

    pass

#=============================================================================
# A simple model for included cssfiles and another for jsfiles.
#=============================================================================

class CssOrJsFiles(Model):

    class Meta:
        abstract = True

    filepath = fields.nameField()

    @classmethod
    def new(cls, filepath):
        css_or_js_file, _created = cls.objects.select_related().get_or_create(filepath=filepath)
        return css_or_js_file

class CssFiles(CssOrJsFiles):
    pass

class JsFiles(CssOrJsFiles):
    pass

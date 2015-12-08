from __future__ import absolute_import

#=============================================================================
# Standard library imports
#=============================================================================
from collections import OrderedDict, Counter
import logging

#=============================================================================
# Django imports
#=============================================================================
from django.db.models import Model
from django.template import Context, loader
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.conf import settings

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core.utils import strings, django, datetime, numerical
from apps.core.models import (OrderedGenericElementToContainerModel,
                              OrderedGenericElementToContainerModelManager,
                              GenericElementToContainerModel)
from apps.presenter.models import LiveExperimentSession
from apps.archives.conf import data_export_conf
from apps.dataexport.utils import safe_export_data

#================================ End Imports ================================

#=============================================================================
# *Session* Widget, Slide and Playlist abstract base models.
#=============================================================================

logger = logging.getLogger('wilhelm')

class SessionModel(Model):

    ''' The abstract base class for all session models. '''

    class Meta:
        abstract = True

    uid = models.CharField(max_length=settings.UID_LENGTH,
                           primary_key=True)

    initialized = models.BooleanField(default=False)
    datetime_initialized = models.DateTimeField(null=True)

    started = models.BooleanField(default=False)
    datetime_started = models.DateTimeField(null=True)

    completed = models.BooleanField(default=False)
    datetime_completed = models.DateTimeField(null=True)

    @classmethod
    def initialize(cls):

        session_model = cls(uid = django.uid())
        session_model.initialized = True
        session_model.datetime_initialized = datetime.now()
        session_model.save()

        return session_model

    def set_started(self):

        self.started = True
        self.datetime_started = datetime.now()
        self.save()

    def set_completed(self):

        self.completed = True
        self.datetime_completed = datetime.now()
        self.save()

    def set_parent_model(self, widget_slide_playlist, model):

        _ct = ContentType.objects.get_for_model(model)
        _uid = model.uid

        setattr(self, widget_slide_playlist+'_ct', _ct)
        setattr(self, widget_slide_playlist+'_uid', _uid)

        self.save()

    def data_export(self):

        export_dict = OrderedDict()

        for key, f in [
                (data_export_conf.object_type, lambda: 'Unknown'),
                (data_export_conf.object_name, lambda: 'Name'),
                (data_export_conf.object_initialized, lambda: self.initialized),
                (data_export_conf.object_initialization_time, 
                 lambda: self.datetime_initialized),
                (data_export_conf.object_started, lambda: self.started),
                (data_export_conf.object_start_time, lambda: self.datetime_started),
                (data_export_conf.object_completed, lambda: self.completed),
                (data_export_conf.object_completed_time, 
                 lambda: self.datetime_completed)
        ]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict


class SessionWidget(SessionModel):

    class Meta:
        abstract = True

    widget_ct = models.ForeignKey(ContentType,
                                  related_name\
                                  = '%(app_label)s_%(class)s_as_widget',
                                  null=True)

    widget_uid = models.CharField(max_length=settings.UID_LENGTH, null=True)
    widget_fk = GenericForeignKey('widget_ct', 'widget_uid')


    @classmethod
    def new(cls, widget):
        return cls._new(widget)

    @classmethod
    def _new(cls, widget):

        '''
        Start a new widget session. Set its parent to be a widget model
        instance.
        '''

        session_widget = cls.initialize()
        session_widget.set_parent_model('widget', widget)

        return session_widget

    @property
    def widget(self):
        ''' A convenience to get the widget generic foreign key. '''
        widget_model = self.widget_ct.model_class()
        return widget_model.objects.select_related().get(uid = self.widget_uid)

    def get(self):

        '''
        By default, return the widget's data.
        '''
        self.set_started()

        return self.widget.get_widget_data()

    def post(self, data):

        '''
        By default, do nothing.
        '''

        pass

    def data_export(self):

        export_dict = super(SessionWidget, self).data_export()

        for key, f in [
                (data_export_conf.object_type, 
                 lambda: data_export_conf.widget_type),
                (data_export_conf.object_name,
                 lambda: self.widget.widgettype.name)
        ]:
            
            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict


    def feedback(self):

        """
        Override instances.
        """

        return None

class SessionSlide(SessionModel):

    class Meta:
        abstract = True

    slide_ct = models.ForeignKey(ContentType,
                                 related_name\
                                 = '%(app_label)s_%(class)s_as_slide',
                                 null=True)

    slide_uid = models.CharField(max_length=settings.UID_LENGTH, null=True)
    slide_fk = GenericForeignKey('slide_ct', 'slide_uid')

    ping_uid = models.CharField(primary_key=False, null=True,
                                max_length=settings.UID_LENGTH)

    live_session = models.ForeignKey(LiveExperimentSession, null=True)

    def set_live_session(self, live_session):
        
        logger.debug(
            'Assigning live_session %s to session_slide %s' % (live_session.uid,
                                                               self.uid)
        )

        self.live_session = live_session
        self.save()

    @classmethod
    def new(cls, slide):
        return cls._new(slide)

    @classmethod
    def _new(cls, slide):


        session_slide = cls.initialize()
        session_slide.set_parent_model('slide', slide)

        logger.debug('Creating session slide %s now.' % session_slide.uid)

        for rank, widget in enumerate(slide.widgets):

            session_widget = widget.new_session_model()

            SessionWidgetAndSlideJoinModel.new(session_slide, 
                                               widget.name, 
                                               session_widget, 
                                               rank)

        return session_slide

    @property
    def slide(self):
        slide_model = self.slide_ct.model_class()
        return slide_model.objects.select_related().get(uid = self.slide_uid)


    def get_session_widget(self, widget_name):

        '''
        Get the session widget contained in this session slide whose name is
        `widget_name`.
        '''

        # TODO (Wed Sep 24 01:56:07 2014): We need to add in some checks here.
        # Currently, if you add in the wrong widget_name, the whole thing
        # breaks silently.

        sessionwidget_sessionslide_maps\
          = SessionWidgetAndSlideJoinModel.objects.filter_by_container(self)\
          .filter(widget_name = widget_name)

        sessionwidget_sessionslide_map = sessionwidget_sessionslide_maps[0]

        session_widget_model\
            = sessionwidget_sessionslide_map.element_ct.model_class()

        return session_widget_model.objects.select_related().get(
            uid = sessionwidget_sessionslide_map.element_uid
        )

    def get_session_widgets(self):

        session_widgets = []

        for sessionwidget_sessionslide_map in\
                SessionWidgetAndSlideJoinModel.objects.filter_by_container(self):

            session_widget_model\
                = sessionwidget_sessionslide_map.element_ct.model_class()

            session_widgets.append(session_widget_model.objects.select_related().get(
                uid = sessionwidget_sessionslide_map.element_uid
                )
            )

        return tuple(session_widgets)


    def set_ping_uid(self, ping_uid):
        self.ping_uid = ping_uid
        self.save()

    def render(self):
        ''' Render the slide's html template.
        We are assuming that slide_uid is assigned. 
        '''

        template_data = self.slide.get_template_data()
        template_data['ping_uid'] = self.ping_uid

        template = loader.get_template(self.slide.slide_type.htmltemplate)
        context = Context(template_data)
        
        return template.render(context)

    @property
    def ping_uid_short(self):
        return self.ping_uid[:settings.UID_SHORT_LENGTH]

    def data_export(self):

        export_dict = super(SessionSlide, self).data_export()

        for key, f in [
                (data_export_conf.object_type, lambda: data_export_conf.slide_type),
                (data_export_conf.object_name, lambda: self.slide.slide_type.name),
                ('slide_live_session', lambda: self.live_session.uid),
                (data_export_conf.slide_widgets, 
                 lambda: [session_widget.data_export() 
                          for session_widget in self.get_session_widgets()])]:

            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict

    def feedback(self):

        """
        Return the feedback summaries of the constituent widgets.
        """

        return {session_widget.widget.name: session_widget.feedback()
                for session_widget in self.get_session_widgets()}


class SessionPlaylist(SessionModel):

    '''
    The playlist of an experiment session.

    '''

    #========================================================================
    class Meta:
        abstract = True
    #========================================================================

    current_slide_rank = models.PositiveIntegerField(null=True)

    playlist_ct = models.ForeignKey(ContentType,
                                    related_name\
                                    = '%(app_label)s_%(class)s_as_playlist',
                                    null=True)

    playlist_uid = models.CharField(max_length=settings.UID_LENGTH, null=True)
    playlist_fk = GenericForeignKey('playlist_ct', 'playlist_uid')

    shuffle = True

    @classmethod
    def new(cls, playlist):
        return cls._new(playlist)

    @classmethod
    def _new(cls, playlist):

        session_playlist = cls.initialize()

        session_playlist.set_parent_model('playlist', playlist)
        
        session_slides = [slide.new_session_model() for slide in playlist.slides]

        if cls.shuffle:
            numerical.shuffle(session_slides)

        for i, session_slide in enumerate(session_slides):

            SessionSlideAndPlaylistJoinModel.new(container=session_playlist, 
                                                 element=session_slide, 
                                                 rank=i)

        return session_playlist

    def iterate(self):

        if self.is_slides_remaining:

            if self.current_slide_rank is None:
                self.current_slide_rank = 0
            else:
                self.current_slide_rank += 1

            self.start_nowplaying()
            
            self.save()

            return self.current_slide

    #=======================================================================
    # Properties. Most of these are interfaces to SlideAndPlaylistJoinModel.
    #=======================================================================
    @property
    def playlist(self):
        playlist = self.playlist_ct.model_class()
        return playlist.objects.select_related().get(uid = self.playlist_uid)

    @property
    def is_nowplaying(self):
        '''
        Has the current slide started and not yet finished?
        '''
        return self.current_slide_in_playlist.started\
            and not self.current_slide_in_playlist.completed

    @property
    def is_current_slide_started(self):
        '''
        Is the current slide started?
        '''
        return self.current_slide_in_playlist.started

    @property
    def is_current_slide_completed(self):
        '''
        Is the current slide completed?
        '''
        return self.current_slide_in_playlist.completed

    @property
    def datetime_current_slide_started(self):
        '''If the current slide has been started, when was it started.'''
        if self.is_current_slide_started:
            return self.current_slide_in_playlist.datetime_started

    @property
    def datetime_current_slide_completed(self):
        '''If the current slide has been completed, when was it completed.'''
        if self.is_current_slide_completed:
            return self.current_slide_in_playlist.datetime_completed

    @property
    def slides_completed(self):
        '''
        How many slides are completed in this playlist.
        '''

        return len(
            self.filter_SlideAndPlaylistJoinModel.filter(completed = True)
        )

    @property
    def filter_SlideAndPlaylistJoinModel(self):

        '''
        Filter the SlideAndPlaylistJoinModel by this playlist.
        '''

        return SessionSlideAndPlaylistJoinModel.objects.filter_by_container(self)


    @property
    def slides_total(self):
        '''
        How many slides are there in total in this playlist.
        '''

        return len(self.filter_SlideAndPlaylistJoinModel)

    @property
    def slides_remaining(self):
        '''
        How many slides are remaining in this playlist.
        '''

        return len(self.filter_SlideAndPlaylistJoinModel.filter(completed=False, 
                                                           started=False)
                   )

    @property
    def is_slides_remaining(self):
        '''
        Return True if there are slides remaining in the playlist.
        '''
        return self.slides_remaining > 0    
    
    @property
    def slides_started_but_not_completed(self):

        '''
        Return all those slides that have started but not completed.
        '''

        return self.filter_SlideAndPlaylistJoinModel.filter(started=True,
                                                       completed=False)

    @property
    def current_slide_in_playlist(self):
        '''
        The slide_in_playlist for the current_slide_rank.
        '''

        return self.get_slide_by_rank(self.current_slide_rank)

    @property
    def current_slide(self):

        session_slide_class\
            = self.current_slide_in_playlist.element_ct.model_class()

        return session_slide_class.objects.select_related().get(uid = self.current_slide_in_playlist.element_uid)

    @property
    def results(self):
        '''
        Collect and merge and return (as configobj string) the results of each
        completed slide in the playlist.
        '''
        pass


    #========================================================================
    # Helper functions.
    #========================================================================
    def get_slide_by_rank(self, rank):

        '''
        Return the `rank`th slide in the playlist.
        '''

        try:
            return SessionSlideAndPlaylistJoinModel\
                .objects.get_element_by_rank_in_container(self, rank)
        except ObjectDoesNotExist as e:
            # This may have happened because rank is None.
            # Prepend the error message to provide extra information.
            raise ObjectDoesNotExist(
                'Can not find a slide with rank %s. %s' % (str(rank), e)
            )

    #====================================================================
    # Some setter helper functions.
    #====================================================================
    def setattr_current_slide_in_playlist(self, attribute, value):

        '''
        For the slide in this playlist with the current_slide_rank, set its
        attribute `attribute` to `value`.
        '''

        current_slide_in_playlist\
            = self.get_slide_by_rank(self.current_slide_rank)
        
        setattr(current_slide_in_playlist, attribute, value)

        current_slide_in_playlist.save()


    def start_nowplaying(self):

        '''
        Start the slide with current_slide_rank, i.e. set started=True.
        '''

        #===================================================================
        # Conditions that must be met before we start nowplaying.
        #===================================================================
        assert len(self.slides_started_but_not_completed) == 0, strings.msg(
            '''There should be no slides that have been started and not
               finished.'''
        )
        # ==================================================================

        self.current_slide_in_playlist.set_started()

        assert self.current_slide_in_playlist.started, 'Should be True'

    def stop_nowplaying(self):
        '''
        Stop the slide with the current_slide_rank (assuming it has been
        started), i.e. set completed=True.
        '''

        started, completed = (self.current_slide_in_playlist.started,
                              self.current_slide_in_playlist.completed)
        
        assert started and (not completed), strings.msg(
                '''Slide should be started but not yet completed.
                    Started is %s, Completed is %s.''' % (started, completed)
        )
        
        self.current_slide_in_playlist.set_completed()

        assert self.current_slide_in_playlist.completed, 'Should be True'

    def data_export(self):

        """
        Return all session slides from this session playlist.

        """
        export_dict = super(SessionPlaylist, self).data_export()

        for key, f in [
                (data_export_conf.object_type, lambda: data_export_conf.playlist_type),
                (data_export_conf.object_name, lambda: 'Generic playlist'),
                (data_export_conf.playlist_slides, 
                 lambda: [element.session_slide.data_export() 
                         for element in self.filter_SlideAndPlaylistJoinModel])
        ]:
            
            export_dict, exception_raised, exception_msg\
                = safe_export_data(export_dict, key, f)

            if exception_raised:
                logger.warning(exception_msg)

        return export_dict


    def feedback(self):

        """

        """
        summary = super(SessionPlaylist, self).data_export()

        summary[data_export_conf.object_type] = data_export_conf.playlist_type
        summary[data_export_conf.object_name] = 'Generic playlist'

        summary[data_export_conf.playlist_slides]\
            = [element.session_slide.feedback() 
               for element in self.filter_SlideAndPlaylistJoinModel]

        test_types = Counter([slide['Test_type'] 
                              for slide in
                              summary[data_export_conf.playlist_slides]])
       
        summary['test_type_counter'] = test_types
            

        return summary

 
#=============================================================================
# The join tables.
#=============================================================================
class SessionJoinModelMixin(Model):

    class Meta:
        abstract = True

    started = models.BooleanField(default=False)
    datetime_started = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    datetime_completed = models.DateTimeField(null=True, blank=True)

    def set_started(self):
        self._set_started_or_completed('started')

    def set_completed(self):
        self._set_started_or_completed('completed')

    def _set_started_or_completed(self, started_or_completed):
        now = datetime.now()
        setattr(self, started_or_completed, True)
        setattr(self, 'datetime_' + started_or_completed, now)
        self.save()

class SessionElementToContainerModel(SessionJoinModelMixin,
                                     GenericElementToContainerModel):

    '''
    A generic join model for session related objects. This can be subclassed to
    produce a Slide and Playlist join model and a slide to widget join model.
    '''

    class Meta:
        abstract = True

    @classmethod
    def new(cls, container, element):

        element_to_container_map\
            = super(SessionElementToContainerModel, cls).new(container,
                                                             element)
        #element_to_container_map.set_started()
        element_to_container_map.save()

        return element_to_container_map

class OrderedSessionElementToContainerModel(SessionJoinModelMixin,
                                            OrderedGenericElementToContainerModel):

    class Meta:
        abstract = True

    @classmethod
    def new(cls, container, element, rank):

        element_to_container_map\
            = super(OrderedSessionElementToContainerModel, cls).new(container,
                                                                    element,
                                                                    rank)
        element_to_container_map.save()

        return element_to_container_map

    objects = OrderedGenericElementToContainerModelManager()

#=============================================================================
# The Slide to playlist join model.
#=============================================================================
class SessionSlideAndPlaylistJoinModel(OrderedSessionElementToContainerModel):

    @property
    def session_slide(self):
        ''' A convenience to get the slide generic foreign key. '''
        element_model = self.element_ct.model_class()
        return element_model.objects.get(uid = self.element_uid)

    def set_completed(self):

        super(SessionSlideAndPlaylistJoinModel, self).set_completed()

        self.session_slide.set_completed()

    def set_started(self):

        super(SessionSlideAndPlaylistJoinModel, self).set_started()

        self.session_slide.set_started()


#=============================================================================
# The Widget to Slide join model.
#=============================================================================
class SessionWidgetAndSlideJoinModel(OrderedSessionElementToContainerModel):
    widget_name = models.CharField(max_length=50, null=True)

    @classmethod
    def new(cls, session_slide, widget_name, session_widget, rank):

        sessionwidget_to_sessionslide_map\
            = super(SessionWidgetAndSlideJoinModel, cls).new(session_slide,
                                                             session_widget,
                                                             rank)

        sessionwidget_to_sessionslide_map.widget_name = widget_name
        sessionwidget_to_sessionslide_map.rank = rank
        sessionwidget_to_sessionslide_map.set_started()
        sessionwidget_to_sessionslide_map.save()

        return sessionwidget_to_sessionslide_map

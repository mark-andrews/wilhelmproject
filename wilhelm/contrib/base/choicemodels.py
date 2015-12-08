from __future__ import absolute_import


#=============================================================================
# Django imports
#=============================================================================
from django.db import models
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core.utils import django

#================================ End Imports ================================
class ChoiceModel(Model):

    class Meta:
        abstract = True
        unique_together = (('sessionwidget_fk', 'stimulus_fk'),)

    uid = models.CharField(primary_key=True,
                           max_length=settings.UID_LENGTH)

    #========================================================================
    sessionwidget_ct = models.ForeignKey(
        ContentType, 
        related_name = '%(app_label)s_%(class)s_as_sessionwidget',
        null=True
    )
    sessionwidget_uid = models.CharField(max_length=settings.UID_LENGTH, 
                                         null=True)

    sessionwidget_fk = GenericForeignKey('sessionwidget_ct',
                                         'sessionwidget_uid')
    #========================================================================

    #========================================================================
    stimulus_ct = models.ForeignKey(
        ContentType, related_name = '%(app_label)s_%(class)s_as_stimulus',
        null=True
    )
    stimulus_uid = models.CharField(max_length=settings.UID_LENGTH, null=True)
    stimulus_fk = GenericForeignKey('stimulus_ct', 'stimulus_uid')
    #========================================================================

    order = models.PositiveSmallIntegerField(null=True)
    stimulus_onset_datetime = models.DateTimeField(null=True)
    response_datetime = models.DateTimeField(null=True)

    @property
    def response_latency(self):

        try:

            return (self.response_datetime 
                    - self.stimulus_onset_datetime).total_seconds()

        except TypeError: 
            return None

    @property
    def sessionwidget(self):
        sessionwidget_model = self.sessionwidget_ct.model_class()
        return sessionwidget_model.objects.get(uid = self.sessionwidget_uid)

    @property
    def stimulus(self):
        stimulus_model = self.stimulus_ct.model_class()
        return stimulus_model.objects.get(uid = self.stimulus_uid)

    @classmethod
    def new(cls,
            sessionwidget,
            stimulus,
            order,
            stimulus_onset_datetime,
            response_datetime):

        sessionwidget_ct = ContentType.objects.get_for_model(sessionwidget)
        sessionwidget_uid = sessionwidget.uid

        stimulus_ct = ContentType.objects.get_for_model(stimulus)
        stimulus_uid = stimulus.uid

        choice_model = cls.objects.create(
                           sessionwidget_ct = sessionwidget_ct,
                           sessionwidget_uid = sessionwidget_uid,
                           stimulus_ct = stimulus_ct,
                           stimulus_uid = stimulus_uid,
                           uid = django.uid(),
                           order = order,
                           stimulus_onset_datetime = stimulus_onset_datetime,
                           response_datetime = response_datetime)

        return choice_model

class BinaryChoiceModel(ChoiceModel):

    class Meta:
        abstract = True

    response = models.NullBooleanField()

    @classmethod
    def new(cls, 
            sessionwidget,
            stimulus,
            response,
            order,
            stimulus_onset_datetime,
            response_datetime):

        binary_choice_model\
            = super(BinaryChoiceModel, cls).new(sessionwidget, 
                                                stimulus, 
                                                order, 
                                                stimulus_onset_datetime, 
                                                response_datetime)

        binary_choice_model.response = response
        binary_choice_model.save()

        return binary_choice_model

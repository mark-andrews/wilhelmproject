from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import operator

#=============================================================================
# Django imports
#=============================================================================
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import Q
from django.db import models
from django.conf import settings

#=============================================================================
# Wilhelm imports.
#=============================================================================
from apps.core import fields

#================================ End Imports ================================

#=============================================================================
# The Element to Container map abstract base class.
#=============================================================================

class GenericElementToContainerModelManager(models.Manager):

    '''
    Manager for the GenericElementToContainerModel.
    '''

    def filter_by_container(self, container):
        '''
        Filter the GenericElementToContainerModel by container.
        I.e., query for all instances of the container.
        '''

        return self.filter(
            container_uid = container.uid,
            container_ct = ContentType.objects.get_for_model(container)
        )

    def filter_by_elements(self, elements):

        '''
        Filter the model by the disjunction of the elements.
        '''
        
        return self.filter(
            reduce(operator.or_, 
                   [Q(element_uid=element.uid,
                      element_ct=ContentType.objects.get_for_model(element))
                    for element in elements])
        )

    def get_elements_of_container(self, container):
        '''
        Return all the elements of a specified container.
        '''
        
        elements = []
        for container_and_element in self.filter_by_container(container):

            element_model = container_and_element.element_ct.model_class()
            element = element_model.objects.get(
                uid = container_and_element.element_uid
            )

            elements.append(element)
 
        return elements

    def get_elements_uid_of_container(self, container):

        return [element.element_uid 
                for element in self.get_elements_of_container(container)]

    def get_containers_with_elements(self, elements):

        '''
        Get the list of containers that contain all and only the elements in
        `elements`.
        '''

        element_and_container_mappings = self.filter_by_elements(elements)
    
        containers = []
        elements_set = set([element.uid for element in elements])

        for container_item in element_and_container_mappings\
                .values('container_ct', 'container_uid').distinct():

            contained_elements_uids = set(map(lambda x : x[0], 
                self.filter(**container_item).values_list('element_uid')
                )
            )

            if contained_elements_uids == elements_set:

               container_model = ContentType.objects.get_for_id(
                    container_item['container_ct']
               ).model_class()

               containers.append(
                    container_model.objects.get(uid = container_item['container_uid'])
               )

        return containers

                # container_element = self.filter(**container_item)
                # container_model = container_element[0].container_ct.model_class()

 
class GenericElementToContainerModel(models.Model):

    '''
    An abstract base class for to make a junction table for generic items.

    It primarily functions to create many-to-many mappings from element to
    container maps, such as many-to-many mappings from instances of slide types
    to instances of playlist types.

    '''

    class Meta:
        abstract = True

    #========================================================================
    # Generic foreign key to point to Container class.
    #========================================================================
    container_ct = models.ForeignKey(ContentType,
                                 null=True,
                                 blank=True,
                                 related_name\
                                 = '%(app_label)s_%(class)s_as_container'
                                )

    container_uid = models.CharField(max_length=settings.UID_LENGTH,
                                null=True,
                                blank=True)

    container = GenericForeignKey('container_ct', 'container_uid')

    #========================================================================
    #========================================================================

    #========================================================================
    # Generic foreign key to point to Element class.
    #========================================================================
    element_ct = models.ForeignKey(ContentType,
                                 null=True,
                                 blank=True, 
                                 related_name\
                                    ='%(app_label)s_%(class)s_as_element'
                                    )

    element_uid = models.CharField(max_length=settings.UID_LENGTH,
                                null=True,
                                blank=True)

    element = GenericForeignKey('element_ct', 'element_uid')

    #========================================================================
    #========================================================================

    objects = GenericElementToContainerModelManager()

    @classmethod
    def new(cls, container, element):
        '''
        Assign element `element` to container `container`.
        '''

        element_to_container_map, _created = cls.objects.get_or_create(
            container_ct = ContentType.objects.get_for_model(container),
            element_ct = ContentType.objects.get_for_model(element),
            container_uid = container.uid,
            element_uid = element.uid
        )

        return element_to_container_map

class OrderedGenericElementToContainerModelManager(GenericElementToContainerModelManager):

    '''
    Manager for the GenericSessionElementToContainerModel.
    This manager is a subclass of GenericElementToContainerModel.
    '''

    def get_element_by_rank_in_container(self, container, k):
        return self.get(
            container_uid = container.uid,
            container_ct = ContentType.objects.get_for_model(container),
            rank = k)

    def get_elements_and_rank_of_container(self, container):
        '''
        Return all the elements of a specified container.
        '''
        
        elements = []
        for container_and_element in self.filter_by_container(container):

            element_model = container_and_element.element_ct.model_class()
            element = element_model.objects.get(
                uid = container_and_element.element_uid
            )

            elements.append((element, container_and_element.rank))
 
        return elements

    def filter_by_container(self, container):
        '''
        Filter the GenericElementToContainerModel by container.
        I.e., query for all instances of the container.
        '''

        return self.filter(
            container_uid = container.uid,
            container_ct = ContentType.objects.get_for_model(container)
        ).order_by('rank')


 
class OrderedGenericElementToContainerModel(GenericElementToContainerModel):

    class Meta:
        abstract = True

    rank = models.PositiveSmallIntegerField(null=True)

    @classmethod
    def new(cls, container, element, rank):

        element_to_container_map, _created = cls.objects.get_or_create(
            container_ct = ContentType.objects.get_for_model(container),
            element_ct = ContentType.objects.get_for_model(element),
            container_uid = container.uid,
            element_uid = element.uid,
            rank = rank
        )

        return element_to_container_map

    objects = OrderedGenericElementToContainerModelManager()

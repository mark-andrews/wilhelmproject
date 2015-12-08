from django.conf.urls import patterns, url

experiment_name_regex = r'[a-zA-Z0-9]+'

urlpatterns = patterns('',
    url(r'^[/]*$', 'apps.research.views.listing', name='project_list'),
#    url(r'^(?P<experiment_name>'+experiment_name_regex+')[/]*$', 
#        'apps.research.views.project_page'),
)

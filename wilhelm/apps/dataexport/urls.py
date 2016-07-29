from django.conf.urls import patterns, url
experiment_name_regex = r'[a-zA-Z0-9]+'

urlpatterns = patterns('',
    url(r'^[/]*$', 'apps.dataexport.views.archive_listing', name='qwerty'),
    url(r'^(?P<experiment_name>'+experiment_name_regex+')[/]*$', 
        'apps.dataexport.views.archive_listing_all_versions', name='qwerty'),
    url(r'^(?P<archive_uid>[0-9a-f]{7})[/]*$', 
        'apps.dataexport.views.archive_download'),
)

from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^[/]*$', 'apps.dataexport.views.archive_listing', name='qwerty'),
    url(r'^(?P<archive_uid>[0-9a-f]{7})[/]*$', 
        'apps.dataexport.views.archive_download'),
)

from django.conf.urls import patterns, url
experiment_name_regex = r'[a-zA-Z0-9]+'

from apps.dataexport import views

urlpatterns = patterns('',
    url(r'^(?P<archive_uid>[0-9a-f]{7})[/]*$', views.archive_download),
    url(r'^[/]*$', views.archive_listing, name='qwerty'),
    url(r'^(?P<experiment_name>'+experiment_name_regex+')[/]*$', views.archive_listing_all_versions, name='qwerty'),
)

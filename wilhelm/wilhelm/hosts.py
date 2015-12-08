from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www', settings.ROOT_URLCONF, name='www'),
    host(r'data', 'apps.dataexport.urls', name='www2'),
    host(r'research', 'apps.research.urls', name='research'),
)

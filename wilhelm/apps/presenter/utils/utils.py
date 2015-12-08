from __future__ import absolute_import

#=============================================================================
# Standard library imports.
#=============================================================================
import logging

#=============================================================================
# Third part imports
#=============================================================================
from ipware.ip import get_real_ip

#=============================================================================
# Django imports.
#=============================================================================
from django.contrib.gis.geoip import GeoIP

#================================ End Imports ================================

logger = logging.getLogger('wilhelm')


def get_ip_address(request):

    return get_real_ip(request)

def get_geoip_info(ip_address):

    # These need to match the geoip fields in models.LiveExperimentSession.
    geoip_info = dict(city = None,
                      country_name = None,
                      country_code = None,
                      country_code_alt = None,
                      longitude = None,
                      latitude = None)

    try:

        g = GeoIP()
        city_information = g.city(ip_address)

        for key in geoip_info:
            if key in city_information and city_information[key]: # if not None
                geoip_info[key] = city_information[key]

    except Exception as e:
        exception_type = e.__class__.__name__
        logger.warning(
            'Could not get GeoIP information. Exception %s. Msg %s.'\
            % (exception_type, e.message))

    return geoip_info

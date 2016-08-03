from __future__ import absolute_import

import datetime
import json

isoformat = '%Y-%m-%d %H:%M:%S' # YYYY-MM-DD HH:MM:SS 
indent_level = 2

def data_export_filter(obj):

    """ How to handle un-json-able data types.

    Wrap very long (>70) lines.

    """


    if type(obj) is datetime.datetime:

        return obj.strftime(isoformat)

def dumps(python_object):

    return json.dumps(python_object,
                      default=data_export_filter,
                      indent=indent_level)

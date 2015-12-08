from __future__ import absolute_import

#================================ End Imports ================================

def filter_by_includes(widget_or_slide_type_queryset, cssfiles, jsfiles):

    '''
    Recursively filter a slide or widget type based on the listed cssfiles and
    jsfiles.
    '''

    if cssfiles:

        for filepath in cssfiles:
            widget_or_slide_type_queryset\
                = widget_or_slide_type_queryset.filter(cssfiles__filepath = filepath)

    if jsfiles:

        for filepath in jsfiles:
            widget_or_slide_type_queryset\
                = widget_or_slide_type_queryset.filter(jsfiles__filepath = filepath)

    return widget_or_slide_type_queryset

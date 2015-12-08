from django import template

register = template.Library()


@register.filter
def next_widget_js_object_name(widget_list, current_widget):
    return widget_list[current_widget + 1]

@register.filter
def joinby(value, arg):
    return arg.join(value)

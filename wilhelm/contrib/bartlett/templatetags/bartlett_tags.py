from django import template

register = template.Library()

@register.filter
def memorandumname(value):
    if value == 'Text':
        return 'text'
    elif value == 'Wordlist':
        return 'word list'

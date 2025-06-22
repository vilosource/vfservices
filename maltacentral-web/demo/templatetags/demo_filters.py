from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if dictionary is None:
        return None
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    try:
        return dictionary[key]
    except (KeyError, TypeError, IndexError):
        return None

@register.filter
@stringfilter
def replace(value, arg):
    """Replace all occurrences of arg in value"""
    if arg:
        pieces = arg.split(',')
        if len(pieces) == 2:
            return value.replace(pieces[0], pieces[1])
    return value
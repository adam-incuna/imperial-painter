from django import template


register = template.Library()


@register.filter
def index(List, i):
    try:
        return List[int(i)]
    except IndexError:
        return ''
    except TypeError:
        return ''


@register.filter
def lookup(dictionary, key):
    return dictionary.get(key)
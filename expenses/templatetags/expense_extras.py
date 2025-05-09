from django import template

register = template.Library()

@register.filter
def get_item(lst, i):
    try:
        return lst[i]
    except:
        return None

@register.filter
def get_range(count):
    return range(count)
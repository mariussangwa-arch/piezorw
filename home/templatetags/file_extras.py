# home/templatetags/file_extras.py
from django import template

register = template.Library()

@register.filter
def in_list(value, arg):
    """Check if value is in comma-separated list"""
    if not value or not arg:
        return False
    items = [item.strip() for item in arg.split(',')]
    return str(value) in items

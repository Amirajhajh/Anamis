from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """
    بررسی می‌کند که رشته 'value' با رشته 'arg' تمام می‌شود یا خیر.
    """
    if not value:
        return False
    return value.lower().endswith(arg.lower())

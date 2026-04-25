from django import template

register = template.Library()


@register.filter
def to_range(value):
    """Return range(value) for use in {% for %} loops — e.g. to generate N empty cells."""
    try:
        return range(int(value))
    except (TypeError, ValueError):
        return range(0)

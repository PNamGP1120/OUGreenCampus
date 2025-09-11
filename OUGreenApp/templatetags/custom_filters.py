from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Cho phép lấy giá trị của dict bằng key trong template"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

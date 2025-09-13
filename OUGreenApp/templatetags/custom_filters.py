from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Cho phép lấy giá trị của dict bằng key trong template"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def zip_lists(a, b):
    """Zip hai danh sách để lặp song song trong template"""
    return zip(a, b)

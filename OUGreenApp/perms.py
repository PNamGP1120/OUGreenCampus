from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Chỉ cho phép user có role = 'admin'
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsEditorOrAdmin(permissions.BasePermission):
    """
    Cho phép user có role = 'editor' hoặc 'admin'
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['editor', 'admin'])


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Cho phép GET cho tất cả, nhưng chỉ owner hoặc admin mới được sửa/xóa
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(obj, "user") and (obj.user == request.user or request.user.role == 'admin')

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Доступ разрешён только владельцу объекта."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Пользовательское разрешение, чтобы только владелец объекта мог редактировать его.
    """
    def has_object_permission(self, request, view, obj):
        # Права на чтение разрешены для любых запросов,
        # поэтому мы всегда будем разрешать запросы GET, HEAD или OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Поле, определяющее владельца, может быть как user, так и owner,
        # в зависимости от модели
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False
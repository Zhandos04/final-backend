# api/views/user_views.py
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from api.serializers.user_serializers import UserSerializer, RegisterSerializer
from api.throttling import UserRateThrottle, AnonRateThrottle
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API для просмотра и обновления профиля пользователя.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user

    # Кэшируем результат на короткое время для частых запросов профиля
    @method_decorator(cache_page(60))  # 1 минута кэширования
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RegisterView(generics.CreateAPIView):
    """
    API для регистрации новых пользователей.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Используем атомарную транзакцию для создания пользователя
        user = serializer.save()

        # Создаем JWT токен для пользователя
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': serializer.data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            },
            'message': 'Пользователь успешно зарегистрирован'
        }, status=status.HTTP_201_CREATED)


class LogoutView(views.APIView):
    """
    API для выхода из системы.
    Поддерживает как JWT token blacklisting, так и сессионный logout.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            # Проверяем, содержит ли запрос refresh token
            refresh_token = request.data.get("refresh")

            if refresh_token:
                # Если есть refresh token, блокируем его (JWT logout)
                token = RefreshToken(refresh_token)
                token.blacklist()
            else:
                # Если нет refresh token, используем Django logout (session-based)
                from django.contrib.auth import logout
                logout(request)

            return Response({
                "status": "success",
                "message": "Успешный выход из системы"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Ошибка при выходе из системы",
                "details": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
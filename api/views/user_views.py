# api/views/user_views.py (Модифицированная версия без отправки email)
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from api.serializers.user_serializers import UserSerializer, RegisterSerializer
from api.throttling import UserRateThrottle, AnonRateThrottle

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API для просмотра и обновления профиля пользователя.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get_object(self):
        return self.request.user

class RegisterView(generics.CreateAPIView):
    """
    API для регистрации новых пользователей.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Создаем JWT токен для пользователя
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
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
            if 'refresh' in request.data:
                # Если есть refresh token, блокируем его (JWT logout)
                refresh_token = request.data["refresh"]
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Успешный выход из системы"}, status=status.HTTP_200_OK)
            else:
                # Если нет refresh token, используем Django logout (session-based)
                from django.contrib.auth import logout
                logout(request)
                return Response({"message": "Успешный выход из системы"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
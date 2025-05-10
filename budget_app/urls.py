# budget_app/urls.py (обновленный)
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

# Документация Swagger/OpenAPI
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

swagger_info = openapi.Info(
    title="Budget Tracker API",
    default_version='v1',
    description="API для управления личными финансами",
    terms_of_service="https://www.example.com/terms/",
    contact=openapi.Contact(email="contact@example.com"),
    license=openapi.License(name="BSD License"),
)

schema_view = get_schema_view(
    swagger_info,
    public=True,
    permission_classes=[permissions.AllowAny],
    url=None if settings.DEBUG else "https://final-backend-production-7ed9.up.railway.app",
    validators=['flex', 'ssv'],
    patterns=[path('api/v1/', include('api.urls'))],
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('expenses/', include('expenses.urls')),
    path('users/', include('users.urls')),
    
    # API URLs
    path('api/v1/', include('api.urls')),
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Конфигурация для статических и медиа файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Добавляем silk для профилирования в режиме разработки
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]